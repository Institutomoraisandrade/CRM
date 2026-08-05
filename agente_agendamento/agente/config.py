"""Leitura e validação do arquivo de configuração (TOML)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agenda.arquivo import AgendaArquivo
from .agenda.base import Agenda
from .agendador import Agendador, JanelaDeAtendimento
from .entrega.email import EnviadorEmail, ErroDeEnvio
from .fontes.base import FontePacientes
from .fontes.liveclin_csv import FonteLiveClin
from .fontes.planilha import Planilha, PlanilhaArquivo, PlanilhaGoogleSheets
from .fontes.webdiet_csv import FonteWebDiet
from .modelos import Plano
from .planos import catalogo_de_config

HORARIOS_PADRAO = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]


class ErroDeConfig(Exception):
    """Configuração ausente, incompleta ou inconsistente."""


@dataclass
class Config:
    raiz: Path
    fonte: dict[str, Any]
    agenda: dict[str, Any]
    planos: dict[str, Plano]
    notificacoes: dict[str, Any] = field(default_factory=dict)
    email: dict[str, Any] = field(default_factory=dict)
    webdiet: dict[str, Any] = field(default_factory=dict)
    filtro: dict[str, Any] = field(default_factory=dict)
    botconversa: dict[str, Any] = field(default_factory=dict)

    def caminho_relativo(self, valor: str) -> Path:
        caminho = Path(valor).expanduser()
        return caminho if caminho.is_absolute() else (self.raiz / caminho)

    def _planilha(self, secao: dict[str, Any], rotulo: str) -> Planilha:
        """Monta a origem da planilha: arquivo em disco ou Google Sheets."""
        tipo = secao.get("tipo", "arquivo")
        if tipo in ("arquivo", "liveclin_csv", "webdiet_csv", "csv"):
            caminho = secao.get("caminho")
            if not caminho:
                raise ErroDeConfig(
                    f"defina {rotulo}.caminho apontando para a planilha, "
                    f"ou use {rotulo}.tipo = \"google_sheets\"."
                )
            return PlanilhaArquivo(self.caminho_relativo(caminho))

        if tipo == "google_sheets":
            google = secao.get("google", {})
            identificador = secao.get("spreadsheet_id") or google.get("spreadsheet_id")
            if not identificador:
                raise ErroDeConfig(
                    f"defina {rotulo}.spreadsheet_id — é o trecho da URL da planilha "
                    "entre /d/ e /edit."
                )
            return PlanilhaGoogleSheets(
                spreadsheet_id=identificador,
                aba=secao.get("aba") or google.get("aba"),
                credenciais=self.caminho_relativo(
                    google.get("credenciais", "credentials.json")
                ),
                token=self.caminho_relativo(google.get("token", "token_sheets.json")),
            )

        raise ErroDeConfig(
            f"{rotulo}.tipo {tipo!r} desconhecido. Use \"arquivo\" ou \"google_sheets\"."
        )

    def construir_fonte(self) -> FontePacientes:
        return FonteLiveClin(
            planilha=self._planilha(self.fonte, "fonte"),
            colunas=self.fonte.get("colunas"),
            catalogo=self.planos,
        )

    def construir_agenda(self) -> Agenda:
        tipo = self.agenda.get("tipo", "arquivo")
        if tipo == "arquivo":
            return AgendaArquivo(self.caminho_relativo(self.agenda.get("caminho", "agenda_local.json")))
        if tipo == "google_calendar":
            from .agenda.google_calendar import AgendaGoogleCalendar

            google = self.agenda.get("google", {})
            return AgendaGoogleCalendar(
                calendar_id=google.get("calendar_id", "primary"),
                credenciais=self.caminho_relativo(google.get("credenciais", "credentials.json")),
                token=self.caminho_relativo(google.get("token", "token.json")),
                fuso=self.agenda.get("fuso", "America/Sao_Paulo"),
            )
        raise ErroDeConfig(
            f"agenda.tipo {tipo!r} desconhecido. Use 'arquivo' ou 'google_calendar'."
        )

    def construir_janela(self) -> JanelaDeAtendimento:
        try:
            return JanelaDeAtendimento(
                dias_semana=self.agenda.get("dias_semana", [1, 2, 3, 4, 5]),
                horarios=self.agenda.get("horarios", HORARIOS_PADRAO),
                duracao_min=int(self.agenda.get("duracao_min", 50)),
                fuso=self.agenda.get("fuso", "America/Sao_Paulo"),
            )
        except (ValueError, KeyError) as erro:
            raise ErroDeConfig(str(erro)) from erro

    def construir_fonte_webdiet(self) -> FonteWebDiet | None:
        """Fonte das avaliações físicas; ``None`` quando não configurada."""
        if not self.webdiet.get("caminho") and not self.webdiet.get("spreadsheet_id"):
            return None
        return FonteWebDiet(
            planilha=self._planilha(self.webdiet, "webdiet"),
            colunas=self.webdiet.get("colunas"),
        )

    def construir_enviador(self) -> EnviadorEmail:
        if not self.email:
            raise ErroDeConfig(
                "não há seção [email] no config.toml. Copie a do config.exemplo.toml "
                "e preencha remetente e destinatarios."
            )
        destinatarios = self.email.get("destinatarios") or []
        if isinstance(destinatarios, str):
            destinatarios = [destinatarios]
        try:
            return EnviadorEmail(
                remetente=self.email.get("remetente", ""),
                destinatarios=list(destinatarios),
                servidor=self.email.get("servidor", "smtp.gmail.com"),
                porta=int(self.email.get("porta", 587)),
                usuario=self.email.get("usuario") or None,
                variavel_senha=self.email.get("variavel_senha", "AGENTE_EMAIL_SENHA"),
                nome_remetente=self.email.get("nome_remetente", "Agente de agendamento"),
            )
        except ErroDeEnvio as erro:
            raise ErroDeConfig(str(erro)) from erro

    def construir_agendador(self) -> Agendador:
        try:
            return Agendador(
                agenda=self.construir_agenda(),
                janela=self.construir_janela(),
                dias_de_busca=int(self.agenda.get("dias_de_busca", 7)),
                antecedencia_horas=int(self.agenda.get("antecedencia_horas", 24)),
                preferencia=self.agenda.get("preferencia", "proximo_do_limite"),
                dias_recuperacao=int(self.agenda.get("dias_recuperacao", 7)),
            )
        except ValueError as erro:
            raise ErroDeConfig(str(erro)) from erro


def carregar_config(caminho: str | Path) -> Config:
    arquivo = Path(caminho).expanduser()
    if not arquivo.exists():
        raise ErroDeConfig(
            f"não encontrei {arquivo}. Copie config.exemplo.toml para config.toml "
            "e preencha com os seus dados."
        )
    try:
        dados = tomllib.loads(arquivo.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as erro:
        raise ErroDeConfig(f"{arquivo} tem TOML inválido: {erro}") from erro

    return Config(
        raiz=arquivo.parent.resolve(),
        fonte=dados.get("fonte", {}),
        agenda=dados.get("agenda", {}),
        planos=catalogo_de_config(dados.get("planos")),
        notificacoes=dados.get("notificacoes", {}),
        email=dados.get("email", {}),
        webdiet=dados.get("webdiet", {}),
        filtro=dados.get("filtro", {}),
        botconversa=dados.get("botconversa", {}),
    )
