"""Quem precisa ser agendado agora, e por quê.

Junta três sinais numa fila única: o limite de 30 dias estourado, o
déficit de consultas do plano e o limite chegando nos próximos dias.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .consultas import Cruzamento, ResumoConsultas
from .modelos import Agendamento, SituacaoAgendamento
from .regras import INTERVALO_MAXIMO_DIAS

# Dentro de quantos dias o limite já é considerado urgente.
JANELA_URGENTE_DIAS = 7


@dataclass
class ItemPrioridade:
    agendamento: Agendamento
    resumo: ResumoConsultas | None
    motivos: list[str] = field(default_factory=list)
    peso: int = 9

    @property
    def paciente(self):
        return self.agendamento.paciente

    @property
    def motivo_principal(self) -> str:
        return self.motivos[0] if self.motivos else ""


def _texto_dias(dias: int) -> str:
    return f"{dias} dia" if abs(dias) == 1 else f"{dias} dias"


def montar_fila(
    agendamentos: list[Agendamento],
    cruzamento: Cruzamento | None,
    hoje: date | None = None,
) -> list[ItemPrioridade]:
    """Fila de quem precisa ser agendado, do mais urgente para o menos."""
    hoje = hoje or date.today()
    fila: list[ItemPrioridade] = []

    for agendamento in agendamentos:
        if agendamento.situacao in (
            SituacaoAgendamento.IGNORADO,
            SituacaoAgendamento.JA_AGENDADO,
        ):
            continue

        paciente = agendamento.paciente
        resumo = cruzamento.de(paciente) if cruzamento else None
        motivos: list[str] = []
        peso = 9

        if agendamento.situacao is SituacaoAgendamento.ATRASADO:
            atraso = (hoje - agendamento.limite).days if agendamento.limite else 0
            if paciente.ultima_consulta is None:
                # Sem última consulta o limite sai do início do plano, e
                # afirmar "passou N dias" seria inventar um atraso que
                # ninguém pode confirmar.
                desde = (hoje - paciente.plano_inicio).days
                motivos.append(
                    f"sem consulta registrada desde o início do plano, há "
                    f"{_texto_dias(desde)} — confirmar no WebDiet"
                )
                peso = min(peso, 5)
            else:
                motivos.append(
                    f"passou {_texto_dias(atraso)} do limite de "
                    f"{INTERVALO_MAXIMO_DIAS} dias"
                    if atraso > 0
                    else f"retorno fora do limite de {INTERVALO_MAXIMO_DIAS} dias"
                )
                peso = min(peso, 0)

        if agendamento.situacao is SituacaoAgendamento.SEM_VAGA:
            motivos.append("sem horário livre antes do limite")
            peso = min(peso, 1)

        if resumo is not None and resumo.esgotadas_cedo(hoje):
            total = resumo.previstas_total
            plural = "consulta" if total == 1 else "consultas"
            motivos.append(
                f"já usou as {total} {plural} do plano, que ainda vale até "
                f"{agendamento.paciente.plano_fim:%d/%m/%Y} — renovar ou liberar avulsa"
            )
            peso = min(peso, 3)

        if resumo is not None and resumo.deficit > 0:
            motivos.append(
                f"{resumo.deficit} consulta(s) a menos do que o plano previa "
                f"({resumo.realizadas} de {resumo.previstas_ate_hoje} até hoje)"
            )
            peso = min(peso, 2)

        if agendamento.situacao is SituacaoAgendamento.PLANO_VENCIDO:
            motivos.append("plano vencido — renovar antes de marcar")
            peso = min(peso, 3)

        if agendamento.limite is not None and agendamento.situacao in (
            SituacaoAgendamento.AGENDAVEL,
            SituacaoAgendamento.SEM_VAGA,
        ):
            faltam = (agendamento.limite - hoje).days
            if 0 <= faltam <= JANELA_URGENTE_DIAS:
                motivos.append(
                    "limite vence hoje"
                    if faltam == 0
                    else f"limite vence em {_texto_dias(faltam)}"
                )
                peso = min(peso, 4)

        if not motivos:
            continue

        fila.append(ItemPrioridade(agendamento, resumo, motivos, peso))

    fila.sort(
        key=lambda item: (
            item.peso,
            item.agendamento.limite or date.max,
            item.paciente.nome,
        )
    )
    return fila
