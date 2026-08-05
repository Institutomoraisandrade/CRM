"""Cruzamento entre planos (LiveClin) e consultas realizadas (WebDiet).

Cada avaliação física do WebDiet conta como uma consulta. Comparando o
que foi feito com o que o plano previa até hoje, sai quem está em dia e
quem ficou para trás.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from .fontes.webdiet_csv import Avaliacao
from .modelos import Paciente, Plano
from .nomes import Correspondencia, casar


def previstas_no_plano(plano: Plano) -> int:
    """Quantas consultas o plano dá direito, conforme o LiveClin."""
    return max(1, plano.consultas)


def previstas_ate(paciente: Paciente, hoje: date) -> int:
    """Quantas consultas já deveriam ter acontecido até hoje.

    As consultas do plano se distribuem pela vigência, e cada uma vence ao
    fim do seu período. Um trimestral dá 3 consultas em 90 dias, uma a
    cada 30: aos 70 dias de plano, duas já deveriam ter acontecido — a
    terceira só vence no dia 90.
    """
    total = previstas_no_plano(paciente.plano)
    if hoje < paciente.plano_inicio:
        return 0
    fim = min(hoje, paciente.plano_fim)
    decorridos = (fim - paciente.plano_inicio).days
    intervalo = paciente.plano.intervalo_medio
    return min(total, int(decorridos // intervalo))


@dataclass
class ResumoConsultas:
    paciente: Paciente
    realizadas: int = 0
    total_historico: int = 0
    previstas_total: int = 0
    previstas_ate_hoje: int = 0
    ultima: date | None = None
    correspondencia: Correspondencia | None = None
    datas: list[date] = field(default_factory=list)

    @property
    def deficit(self) -> int:
        """Quantas consultas faltam para ficar em dia com o plano."""
        return max(0, self.previstas_ate_hoje - self.realizadas)

    @property
    def em_dia(self) -> bool:
        return self.deficit == 0

    @property
    def restantes_no_plano(self) -> int:
        return max(0, self.previstas_total - self.realizadas)

    @property
    def esgotadas(self) -> bool:
        """Já usou todas as consultas a que o plano dá direito."""
        return not self.sem_dados and self.realizadas >= self.previstas_total

    def esgotadas_cedo(self, hoje: date) -> bool:
        """Esgotou as consultas com plano suficiente sobrando para mais uma.

        Num plano mensal, usar a única consulta é o curso normal — só vira
        problema quando ainda cabe outro ciclo de atendimento na vigência.
        """
        if not self.esgotadas:
            return False
        restantes = (self.paciente.plano_fim - hoje).days
        return restantes > self.paciente.plano.intervalo_medio

    @property
    def adiantadas(self) -> int:
        """Consultas feitas além do que o plano previa para esta altura."""
        return max(0, self.realizadas - self.previstas_ate_hoje)

    @property
    def sem_dados(self) -> bool:
        """O paciente não foi encontrado na exportação do WebDiet."""
        return self.correspondencia is None or not self.correspondencia.encontrou

    def resumo(self) -> str:
        return f"{self.realizadas} de {self.previstas_total}"


@dataclass
class Cruzamento:
    resumos: dict[str, ResumoConsultas]
    avisos: list[str] = field(default_factory=list)
    ambiguidades: list[Correspondencia] = field(default_factory=list)
    sem_paciente: list[Correspondencia] = field(default_factory=list)

    def de(self, paciente: Paciente) -> ResumoConsultas | None:
        return self.resumos.get(paciente.nome)


def cruzar(
    pacientes: list[Paciente],
    avaliacoes: list[Avaliacao],
    hoje: date | None = None,
) -> Cruzamento:
    """Associa as avaliações do WebDiet aos pacientes do LiveClin.

    Nomes que ficam ambíguos **não** são atribuídos a ninguém: entram em
    ``ambiguidades`` para conferência humana. Contar a consulta na pessoa
    errada é pior do que não contar.
    """
    hoje = hoje or date.today()

    resumos = {
        p.nome: ResumoConsultas(
            paciente=p,
            previstas_total=previstas_no_plano(p.plano),
            previstas_ate_hoje=previstas_ate(p, hoje),
        )
        for p in pacientes
    }

    por_nome: dict[str, list[date]] = defaultdict(list)
    for avaliacao in avaliacoes:
        por_nome[avaliacao.paciente].append(avaliacao.data)

    nomes_pacientes = [p.nome for p in pacientes]
    cruzamento = Cruzamento(resumos=resumos)

    for nome_webdiet, datas in sorted(por_nome.items()):
        correspondencia = casar(nome_webdiet, nomes_pacientes)

        if correspondencia.ambiguo:
            cruzamento.ambiguidades.append(correspondencia)
            cruzamento.avisos.append(correspondencia.explicar())
            continue
        if not correspondencia.encontrou:
            cruzamento.sem_paciente.append(correspondencia)
            continue

        resumo = resumos[correspondencia.escolhido]
        if resumo.correspondencia is not None:
            # Dois nomes diferentes do WebDiet caíram no mesmo paciente.
            cruzamento.avisos.append(
                f"{nome_webdiet!r} e {resumo.correspondencia.consultado!r} "
                f"apontam para {correspondencia.escolhido!r}; somei as duas."
            )
        else:
            resumo.correspondencia = correspondencia
            if not correspondencia.exato:
                cruzamento.avisos.append(correspondencia.explicar())

        paciente = resumo.paciente
        resumo.total_historico += len(datas)
        no_plano = [
            d for d in datas if paciente.plano_inicio <= d <= paciente.plano_fim
        ]
        resumo.datas.extend(sorted(no_plano))
        resumo.realizadas += len(no_plano)
        candidatas = [d for d in datas if d <= hoje]
        if candidatas:
            mais_recente = max(candidatas)
            if resumo.ultima is None or mais_recente > resumo.ultima:
                resumo.ultima = mais_recente

    return cruzamento


def aplicar_ultima_consulta(cruzamento: Cruzamento) -> list[str]:
    """Adota a última avaliação antropométrica do WebDiet como última consulta.

    O LiveClin guarda plano e prazo; quem sabe a data real do último
    atendimento é o WebDiet. Sem isso o limite de 30 dias seria contado a
    partir do início do plano, que é sempre cedo demais.
    """
    ajustes: list[str] = []
    for resumo in cruzamento.resumos.values():
        if resumo.ultima is None:
            continue
        paciente = resumo.paciente
        anterior = paciente.ultima_consulta
        if anterior == resumo.ultima:
            continue
        paciente.ultima_consulta = resumo.ultima
        if anterior is None:
            ajustes.append(
                f"{paciente.nome}: última consulta {resumo.ultima:%d/%m/%Y} "
                "(do WebDiet)"
            )
        else:
            ajustes.append(
                f"{paciente.nome}: última consulta corrigida de "
                f"{anterior:%d/%m/%Y} para {resumo.ultima:%d/%m/%Y} (do WebDiet)"
            )
    return ajustes
