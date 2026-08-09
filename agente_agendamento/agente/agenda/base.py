"""Contrato dos provedores de agenda."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


class ErroDeAgenda(Exception):
    """Falha ao consultar ou gravar na agenda."""


@dataclass(frozen=True)
class EventoAgenda:
    titulo: str
    inicio: datetime
    fim: datetime


class Agenda(ABC):
    @abstractmethod
    def eventos(self, inicio: datetime, fim: datetime) -> list[EventoAgenda]:
        """Compromissos que tocam a janela consultada, ordenados por início."""

    @abstractmethod
    def criar_evento(
        self,
        titulo: str,
        inicio: datetime,
        fim: datetime,
        descricao: str = "",
    ) -> str:
        """Cria o compromisso e devolve um identificador."""

    def ocupados(self, inicio: datetime, fim: datetime) -> list[tuple[datetime, datetime]]:
        """Intervalos ocupados, derivados dos eventos."""
        return [(e.inicio, e.fim) for e in self.eventos(inicio, fim)]
