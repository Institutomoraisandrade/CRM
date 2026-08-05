"""Agenda local em arquivo JSON.

É o provedor padrão: funciona sem nenhuma credencial, guardando os
compromissos num arquivo na própria máquina. Útil para rodar o agente
antes de conectar o Google Calendar.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from ..util import garantir_fuso
from .base import Agenda, ErroDeAgenda, EventoAgenda


class AgendaArquivo(Agenda):
    def __init__(self, caminho: str | Path) -> None:
        self.caminho = Path(caminho).expanduser()

    def _carregar(self) -> list[dict]:
        if not self.caminho.exists():
            return []
        try:
            dados = json.loads(self.caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as erro:
            raise ErroDeAgenda(f"agenda {self.caminho} tem JSON inválido: {erro}") from erro
        if not isinstance(dados, list):
            raise ErroDeAgenda(f"agenda {self.caminho} deveria conter uma lista de eventos.")
        return dados

    def _gravar(self, eventos: list[dict]) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(
            json.dumps(eventos, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def eventos(self, inicio: datetime, fim: datetime) -> list[EventoAgenda]:
        # Eventos editados à mão podem estar sem fuso; alinha com a janela
        # consultada antes de comparar.
        fuso = inicio.tzinfo
        encontrados: list[EventoAgenda] = []
        for evento in self._carregar():
            try:
                ev_inicio = datetime.fromisoformat(evento["inicio"])
                ev_fim = datetime.fromisoformat(evento["fim"])
            except (KeyError, ValueError) as erro:
                raise ErroDeAgenda(
                    f"evento inválido em {self.caminho}: {evento!r} ({erro})"
                ) from erro
            if fuso is not None:
                ev_inicio = garantir_fuso(ev_inicio, fuso)
                ev_fim = garantir_fuso(ev_fim, fuso)
            if ev_fim > inicio and ev_inicio < fim:
                encontrados.append(
                    EventoAgenda(str(evento.get("titulo", "")), ev_inicio, ev_fim)
                )
        return sorted(encontrados, key=lambda e: e.inicio)

    def criar_evento(
        self, titulo: str, inicio: datetime, fim: datetime, descricao: str = ""
    ) -> str:
        eventos = self._carregar()
        identificador = str(uuid.uuid4())
        eventos.append(
            {
                "id": identificador,
                "titulo": titulo,
                "inicio": inicio.isoformat(),
                "fim": fim.isoformat(),
                "descricao": descricao,
            }
        )
        self._gravar(eventos)
        return identificador
