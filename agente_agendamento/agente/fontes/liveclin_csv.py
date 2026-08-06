"""Leitura da planilha de pacientes do LiveClin.

O LiveClin não oferece API pública, então a origem é a planilha: um
arquivo CSV/XLSX exportado, ou uma aba do Google Sheets lida por OAuth.
Os nomes de coluna variam entre exportações, por isso cada campo aceita
vários apelidos e pode ser sobrescrito na configuração (seção
``[fonte.colunas]``).
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from ..modelos import Paciente, StatusPaciente
from ..planos import CATALOGO_PADRAO, Plano, plano_por_duracao, resolver_plano
from ..util import chave, ler_data, so_digitos
from .base import ErroDeFonte, FontePacientes
from .planilha import Planilha, PlanilhaArquivo

APELIDOS_COLUNA: dict[str, tuple[str, ...]] = {
    "nome": (
        "nome", "paciente", "nome do paciente", "nome completo",
        # Relatório de pacientes do LiveClin (cabeçalhos técnicos).
        "patientreport.headers.full_name",
    ),
    "plano": (
        "plano", "plano selecionado", "tipo de plano", "plano contratado",
        "patientreport.headers.last_service_provided",
    ),
    "plano_inicio": (
        "inicio do plano",
        "data de inicio",
        "data inicio",
        "inicio",
        "inicio do acompanhamento",
        "data de contratacao",
        # Na exportação de serviços, a transação é o início da vigência.
        "data da transacao",
        "data da transacao",
        "data pagamento",
    ),
    "plano_fim": (
        "fim do plano",
        "data de fim",
        "data fim",
        "vencimento",
        "data de vencimento",
        "validade",
        "vigencia",
        "termino",
        "patientreport.headers.service_end_date",
    ),
    "duracao": (
        "duracao (dias)", "duracao dias", "duracao", "dias",
        "patientreport.headers.service_duration_days",
    ),
    "status": (
        "status", "situacao", "tipo de cliente", "status liveclin",
        "patientreport.headers.customer_status",
    ),
    "whatsapp": (
        "whatsapp", "telefone", "celular", "whatsapp do paciente",
        "patientreport.headers.phone_number",
    ),
    "email": ("email", "e-mail", "patientreport.headers.email"),
    "ultima_consulta": (
        "ultima consulta",
        "data da ultima consulta",
        "ultimo atendimento",
        "ultima avaliacao",
    ),
    "etiquetas": ("etiquetas", "etiqueta", "tags", "marcadores"),
    "id_externo": ("id", "codigo", "id do paciente", "patientreport.headers.id"),
}

APELIDOS_STATUS: dict[str, StatusPaciente] = {
    "ativo": StatusPaciente.ATIVO,
    "ativos": StatusPaciente.ATIVO,
    "em acompanhamento": StatusPaciente.ATIVO,
    "pausado": StatusPaciente.PAUSADO,
    "pausados": StatusPaciente.PAUSADO,
    "em pausa": StatusPaciente.PAUSADO,
    "inativo": StatusPaciente.INATIVO,
    "inativos": StatusPaciente.INATIVO,
    "finalizado": StatusPaciente.INATIVO,
    "encerrado": StatusPaciente.INATIVO,
    "cancelado": StatusPaciente.INATIVO,
    # O relatório do LiveClin exporta os status em inglês.
    "active": StatusPaciente.ATIVO,
    "inactive": StatusPaciente.INATIVO,
    "finished": StatusPaciente.INATIVO,
    "paused": StatusPaciente.PAUSADO,
}


class FonteLiveClin(FontePacientes):
    """Lê pacientes de qualquer planilha do LiveClin — arquivo ou Sheets."""

    def __init__(
        self,
        planilha: Planilha,
        colunas: dict[str, str] | None = None,
        catalogo: dict[str, Plano] | None = None,
    ) -> None:
        self.planilha = planilha
        self.colunas_config = {campo: chave(col) for campo, col in (colunas or {}).items()}
        self.catalogo = catalogo if catalogo is not None else dict(CATALOGO_PADRAO)
        self._avisos: list[str] = []

    @property
    def avisos(self) -> list[str]:
        return self._avisos

    def _mapear_cabecalho(self, cabecalhos: Iterable[str]) -> dict[str, str]:
        disponiveis = {chave(c): c for c in cabecalhos if c}
        mapa: dict[str, str] = {}
        for campo, apelidos in APELIDOS_COLUNA.items():
            configurado = self.colunas_config.get(campo)
            if configurado and configurado in disponiveis:
                mapa[campo] = disponiveis[configurado]
                continue
            for apelido in apelidos:
                if apelido in disponiveis:
                    mapa[campo] = disponiveis[apelido]
                    break
        return mapa

    def carregar(self) -> list[Paciente]:
        linhas = self.planilha.linhas()
        if not linhas:
            raise ErroDeFonte(f"a planilha {self.planilha.descricao} está vazia.")

        mapa = self._mapear_cabecalho(linhas[0].keys())
        faltando = [c for c in ("nome", "plano") if c not in mapa]
        if faltando:
            raise ErroDeFonte(
                "não encontrei as colunas obrigatórias "
                + ", ".join(faltando)
                + f" em {self.planilha.descricao}. Colunas lidas: "
                + ", ".join(str(c) for c in linhas[0].keys())
                + ". Configure os nomes reais em [fonte.colunas]."
            )

        pacientes: list[Paciente] = []
        for numero, linha in enumerate(linhas, start=2):
            try:
                paciente = self._montar_paciente(linha, mapa)
            except ValueError as erro:
                self._avisos.append(f"linha {numero} ignorada: {erro}")
                continue
            if paciente is not None:
                pacientes.append(paciente)
        return pacientes

    def _valor(self, linha: dict[str, Any], mapa: dict[str, str], campo: str) -> str | None:
        coluna = mapa.get(campo)
        if coluna is None:
            return None
        bruto = linha.get(coluna)
        if bruto is None:
            return None
        texto = str(bruto).strip()
        return texto or None

    def _duracao(self, linha: dict[str, Any], mapa: dict[str, str]) -> int | None:
        """Lê a coluna de duração em dias, quando existir."""
        bruto = self._valor(linha, mapa, "duracao")
        if not bruto:
            return None
        try:
            dias = int(float(bruto.replace(".", "").replace(",", ".")))
        except ValueError:
            return None
        return dias if dias > 0 else None

    def _montar_paciente(
        self, linha: dict[str, Any], mapa: dict[str, str]
    ) -> Paciente | None:
        nome = self._valor(linha, mapa, "nome")
        if not nome:
            return None

        plano_bruto = self._valor(linha, mapa, "plano")
        dias = self._duracao(linha, mapa)
        tem_data = self._valor(linha, mapa, "plano_inicio") or self._valor(
            linha, mapa, "plano_fim"
        )
        if not plano_bruto and not dias and not tem_data:
            # Cadastro sem nenhum serviço contratado: é lead, não paciente
            # em acompanhamento. Sai da lista sem virar aviso.
            return None

        pelo_nome = resolver_plano(plano_bruto, self.catalogo) if plano_bruto else None
        if dias:
            if pelo_nome is None:
                plano = plano_por_duracao(dias, self.catalogo)
            elif pelo_nome.duracao_dias == dias:
                plano = pelo_nome
            else:
                # A duração da planilha manda nas datas, mas o número de
                # consultas é do tipo de plano: um "Anual" de 365 dias dá
                # as 10 consultas do anual, não 12 por divisão.
                plano = Plano(pelo_nome.nome, dias, consultas=pelo_nome.consultas)
                if abs(dias - pelo_nome.duracao_dias) > 15:
                    self._avisos.append(
                        f"{nome}: plano {plano_bruto!r} costuma valer "
                        f"{pelo_nome.duracao_dias} dias, mas a planilha diz {dias}; "
                        "usei a duração da planilha"
                    )
        else:
            plano = pelo_nome

        if plano is None:
            if not plano_bruto:
                raise ValueError(f"{nome} está sem plano preenchido")
            raise ValueError(
                f"não consegui deduzir a duração do plano {plano_bruto!r} de {nome} "
                "(configure-o em [planos] ou preencha a coluna de duração)"
            )

        inicio = ler_data(self._valor(linha, mapa, "plano_inicio"))
        fim = ler_data(self._valor(linha, mapa, "plano_fim"))
        if inicio is None and fim is None:
            raise ValueError(
                f"{nome} está sem data de início e sem data de fim do plano"
            )
        if inicio is None:
            inicio = fim - timedelta(days=plano.duracao_dias)
        if fim is None:
            fim = plano.data_fim(inicio)
        if fim < inicio:
            raise ValueError(
                f"{nome} tem fim do plano ({fim:%d/%m/%Y}) anterior ao início "
                f"({inicio:%d/%m/%Y})"
            )

        status_bruto = self._valor(linha, mapa, "status")
        status = StatusPaciente.ATIVO
        if status_bruto:
            reconhecido = APELIDOS_STATUS.get(chave(status_bruto))
            if reconhecido is None:
                # Assumir "ativo" em silêncio colocaria na fila de
                # agendamento alguém que talvez já tenha encerrado.
                self._avisos.append(
                    f"status {status_bruto!r} de {nome} não é reconhecido; "
                    "tratei como ativo — confira se a coluna de status é a certa"
                )
            else:
                status = reconhecido

        ultima = ler_data(self._valor(linha, mapa, "ultima_consulta"))
        if ultima is not None and ultima > date.today():
            raise ValueError(
                f"{nome} tem última consulta no futuro ({ultima:%d/%m/%Y})"
            )

        etiquetas_bruto = self._valor(linha, mapa, "etiquetas") or ""
        etiquetas = [e.strip() for e in etiquetas_bruto.replace(";", ",").split(",") if e.strip()]

        return Paciente(
            nome=nome,
            plano=plano,
            plano_inicio=inicio,
            plano_fim=fim,
            status=status,
            whatsapp=so_digitos(self._valor(linha, mapa, "whatsapp")),
            email=self._valor(linha, mapa, "email"),
            ultima_consulta=ultima,
            etiquetas=etiquetas,
            id_externo=self._valor(linha, mapa, "id_externo"),
        )


def FonteLiveClinCSV(
    caminho: str | Path,
    colunas: dict[str, str] | None = None,
    catalogo: dict[str, Plano] | None = None,
) -> FonteLiveClin:
    """Atalho para ler o LiveClin de um arquivo em disco."""
    return FonteLiveClin(PlanilhaArquivo(caminho), colunas, catalogo)
