"""Envio do relatório por e-mail (SMTP).

A senha nunca fica no arquivo de configuração: ela é lida da variável de
ambiente apontada por ``variavel_senha`` (padrão ``AGENTE_EMAIL_SENHA``).
No Gmail, use uma Senha de app — a senha normal da conta não funciona
para SMTP quando a verificação em duas etapas está ativa.
"""

from __future__ import annotations

import mimetypes
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate
from pathlib import Path


def _tipo_do_arquivo(arquivo: Path) -> tuple[str, str]:
    palpite, _ = mimetypes.guess_type(arquivo.name)
    if not palpite:
        return "application", "octet-stream"
    tipo, _, subtipo = palpite.partition("/")
    return tipo, subtipo or "octet-stream"


class ErroDeEnvio(Exception):
    """Falha ao montar ou entregar a mensagem."""


AJUDA_SENHA_APP = (
    "No Gmail com verificação em duas etapas, o SMTP exige uma Senha de app "
    "(16 letras), não a senha da conta. Gere em "
    "https://myaccount.google.com/apppasswords e exporte assim:\n"
    '  export AGENTE_EMAIL_SENHA="suasenhadeapp"'
)


class EnviadorEmail:
    def __init__(
        self,
        remetente: str,
        destinatarios: list[str],
        servidor: str = "smtp.gmail.com",
        porta: int = 587,
        usuario: str | None = None,
        variavel_senha: str = "AGENTE_EMAIL_SENHA",
        nome_remetente: str = "Agente de agendamento",
        timeout: int = 30,
    ) -> None:
        if not remetente:
            raise ErroDeEnvio("defina email.remetente no config.toml")
        if not destinatarios:
            raise ErroDeEnvio("defina email.destinatarios no config.toml")
        self.remetente = remetente
        self.destinatarios = destinatarios
        self.servidor = servidor
        self.porta = int(porta)
        self.usuario = usuario or remetente
        self.variavel_senha = variavel_senha
        self.nome_remetente = nome_remetente
        self.timeout = timeout

    def _senha(self) -> str:
        senha = os.environ.get(self.variavel_senha, "").strip()
        if not senha:
            raise ErroDeEnvio(
                f"a variável de ambiente {self.variavel_senha} está vazia.\n"
                + AJUDA_SENHA_APP
            )
        return senha

    def montar(
        self,
        assunto: str,
        texto: str,
        html: str,
        anexos: list[str | Path] | None = None,
    ) -> EmailMessage:
        mensagem = EmailMessage()
        mensagem["Subject"] = assunto
        mensagem["From"] = formataddr((self.nome_remetente, self.remetente))
        mensagem["To"] = ", ".join(self.destinatarios)
        mensagem["Date"] = formatdate(localtime=True)
        mensagem.set_content(texto)
        mensagem.add_alternative(html, subtype="html")

        for caminho in anexos or []:
            arquivo = Path(caminho).expanduser()
            if not arquivo.exists():
                raise ErroDeEnvio(f"anexo não encontrado: {arquivo}")
            tipo, subtipo = _tipo_do_arquivo(arquivo)
            mensagem.add_attachment(
                arquivo.read_bytes(),
                maintype=tipo,
                subtype=subtipo,
                filename=arquivo.name,
            )
        return mensagem

    def enviar(
        self,
        assunto: str,
        texto: str,
        html: str,
        anexos: list[str | Path] | None = None,
    ) -> list[str]:
        senha = self._senha()
        mensagem = self.montar(assunto, texto, html, anexos)
        contexto = ssl.create_default_context()

        try:
            if self.porta == 465:
                with smtplib.SMTP_SSL(
                    self.servidor, self.porta, timeout=self.timeout, context=contexto
                ) as smtp:
                    smtp.login(self.usuario, senha)
                    smtp.send_message(mensagem)
            else:
                with smtplib.SMTP(self.servidor, self.porta, timeout=self.timeout) as smtp:
                    smtp.starttls(context=contexto)
                    smtp.login(self.usuario, senha)
                    smtp.send_message(mensagem)
        except smtplib.SMTPAuthenticationError as erro:
            raise ErroDeEnvio(
                f"o servidor recusou o login de {self.usuario}.\n{AJUDA_SENHA_APP}\n"
                f"Resposta do servidor: {erro.smtp_error!r}"
            ) from erro
        except (smtplib.SMTPException, OSError) as erro:
            raise ErroDeEnvio(
                f"não consegui falar com {self.servidor}:{self.porta} ({erro})"
            ) from erro

        return list(self.destinatarios)
