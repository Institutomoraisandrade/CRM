"""Agenda no Google Calendar.

Provedor opcional. Exige as bibliotecas oficiais do Google e um
``credentials.json`` de OAuth de aplicativo instalado, gerado no console
do Google Cloud pelo próprio profissional. O agente nunca pede nem
armazena senha do Google: o login acontece no navegador da sua máquina e
o token fica em disco local.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .base import Agenda, ErroDeAgenda, EventoAgenda

ESCOPOS = ["https://www.googleapis.com/auth/calendar"]

_INSTRUCAO = (
    "Para usar o Google Calendar instale as dependências opcionais:\n"
    "  pip install -r requirements-google.txt\n"
    "e gere um credentials.json de OAuth (tipo 'Aplicativo para computador') "
    "em https://console.cloud.google.com/apis/credentials."
)


class AgendaGoogleCalendar(Agenda):
    def __init__(
        self,
        calendar_id: str = "primary",
        credenciais: str | Path = "credentials.json",
        token: str | Path = "token.json",
        fuso: str = "America/Sao_Paulo",
    ) -> None:
        self.calendar_id = calendar_id
        self.credenciais = Path(credenciais).expanduser()
        self.token = Path(token).expanduser()
        self.fuso = fuso
        self._servico = None

    def _obter_servico(self):
        if self._servico is not None:
            return self._servico
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
        except ImportError as erro:
            raise ErroDeAgenda(_INSTRUCAO) from erro

        credencial = None
        if self.token.exists():
            credencial = Credentials.from_authorized_user_file(str(self.token), ESCOPOS)
        if credencial is None or not credencial.valid:
            if credencial and credencial.expired and credencial.refresh_token:
                credencial.refresh(Request())
            else:
                if not self.credenciais.exists():
                    raise ErroDeAgenda(
                        f"não encontrei {self.credenciais}.\n{_INSTRUCAO}"
                    )
                fluxo = InstalledAppFlow.from_client_secrets_file(
                    str(self.credenciais), ESCOPOS
                )
                credencial = fluxo.run_local_server(port=0)
            self.token.write_text(credencial.to_json(), encoding="utf-8")

        self._servico = build("calendar", "v3", credentials=credencial)
        return self._servico

    def eventos(self, inicio: datetime, fim: datetime) -> list[EventoAgenda]:
        servico = self._obter_servico()
        encontrados: list[EventoAgenda] = []
        pagina = None
        while True:
            resposta = (
                servico.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=inicio.isoformat(),
                    timeMax=fim.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                    maxResults=2500,
                    pageToken=pagina,
                )
                .execute()
            )
            for item in resposta.get("items", []):
                if item.get("status") == "cancelled":
                    continue
                if item.get("transparency") == "transparent":
                    # Evento marcado como "disponível" não bloqueia a agenda.
                    continue
                momento = self._intervalo(item, inicio.tzinfo)
                if momento is None:
                    continue
                encontrados.append(
                    EventoAgenda(item.get("summary", ""), momento[0], momento[1])
                )
            pagina = resposta.get("nextPageToken")
            if not pagina:
                break
        return sorted(encontrados, key=lambda e: e.inicio)

    @staticmethod
    def _intervalo(item: dict, fuso) -> tuple[datetime, datetime] | None:
        inicio_bruto = item.get("start", {})
        fim_bruto = item.get("end", {})
        if "dateTime" in inicio_bruto and "dateTime" in fim_bruto:
            return (
                datetime.fromisoformat(inicio_bruto["dateTime"]),
                datetime.fromisoformat(fim_bruto["dateTime"]),
            )
        if "date" in inicio_bruto and "date" in fim_bruto:
            # Evento de dia inteiro ocupa o dia todo.
            inicio = datetime.fromisoformat(inicio_bruto["date"]).replace(tzinfo=fuso)
            fim = datetime.fromisoformat(fim_bruto["date"]).replace(tzinfo=fuso)
            return inicio, fim
        return None

    def criar_evento(
        self, titulo: str, inicio: datetime, fim: datetime, descricao: str = ""
    ) -> str:
        servico = self._obter_servico()
        evento = (
            servico.events()
            .insert(
                calendarId=self.calendar_id,
                body={
                    "summary": titulo,
                    "description": descricao,
                    "start": {"dateTime": inicio.isoformat(), "timeZone": self.fuso},
                    "end": {"dateTime": fim.isoformat(), "timeZone": self.fuso},
                },
            )
            .execute()
        )
        return evento.get("id", "")
