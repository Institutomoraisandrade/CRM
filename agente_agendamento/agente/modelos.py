"""Modelos de domínio do agente de agendamento."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum


class StatusPaciente(str, Enum):
    ATIVO = "ativo"
    PAUSADO = "pausado"
    INATIVO = "inativo"


@dataclass(frozen=True)
class Plano:
    """Tipo de plano de acompanhamento contratado pelo paciente."""

    nome: str
    duracao_dias: int

    def data_fim(self, inicio: date) -> date:
        return inicio + timedelta(days=self.duracao_dias)


@dataclass
class Paciente:
    nome: str
    plano: Plano
    plano_inicio: date
    plano_fim: date
    status: StatusPaciente = StatusPaciente.ATIVO
    whatsapp: str | None = None
    email: str | None = None
    ultima_consulta: date | None = None
    etiquetas: list[str] = field(default_factory=list)
    id_externo: str | None = None

    @property
    def dias_para_vencer(self) -> int:
        """Dias restantes de vigência do plano, contados de hoje."""
        return self.dias_para_vencer_em(date.today())

    def dias_para_vencer_em(self, referencia: date) -> int:
        return (self.plano_fim - referencia).days


class TipoAlerta(str, Enum):
    CHECKIN_15_DIAS = "checkin_15_dias"
    RETORNO_30_DIAS = "retorno_30_dias"
    PLANO_VENCENDO = "plano_vencendo"
    PLANO_VENCIDO = "plano_vencido"
    CONSULTA_ATRASADA = "consulta_atrasada"


@dataclass
class Alerta:
    tipo: TipoAlerta
    paciente: Paciente
    data_referencia: date
    mensagem: str
    destinatarios: list[str] = field(default_factory=lambda: ["profissional"])


class SituacaoAgendamento(str, Enum):
    AGENDAVEL = "agendavel"
    ATRASADO = "atrasado"
    JA_AGENDADO = "ja_agendado"
    SEM_VAGA = "sem_vaga"
    PLANO_VENCIDO = "plano_vencido"
    IGNORADO = "ignorado"


@dataclass
class Agendamento:
    """Proposta de agendamento produzida pelo motor.

    ``inicio`` só é preenchido quando a situação permite marcar a consulta.
    """

    paciente: Paciente
    situacao: SituacaoAgendamento
    limite: date | None = None
    inicio: datetime | None = None
    fim: datetime | None = None
    motivo: str = ""
