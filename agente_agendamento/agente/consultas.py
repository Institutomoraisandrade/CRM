"""Cruzamento entre planos (LiveClin) e consultas realizadas (WebDiet).

Cada avaliação física do WebDiet conta como uma consulta. Comparando o
que foi feito com o que o plano previa até hoje, sai quem está em dia e
quem ficou para trás.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from math import ceil

from .fontes.webdiet_csv import Avaliacao
from .modelos import Paciente
from .nomes import Correspondencia, casar
from .regras import INTERVALO_MAXIMO_DIAS


def previstas_no_plano(duracao_dias: int) -> int:
    """Quantas consultas o plano inteiro prevê, uma a cada 30 dias."""
    return max(1, ceil(duracao_dias / INTERVALO_MAXIMO_DIAS))


def previstas_ate(paciente: Paciente, hoje: date) -> int:
    """Quantas consultas já deveriam ter acontecido até hoje."""
    total = previstas_no_plano(paciente.plano.duracao_dias)
    if hoje < paciente.plano_inicio:
        return 0
    fim = min(hoje, paciente.plano_fim)
    decorridos = (fim - paciente.plano_inicio).days
    return max(1, min(total, decorridos // INTERVALO_MAXIMO_DIAS + 1))


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
            previstas_total=previstas_no_plano(p.plano.duracao_dias),
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
