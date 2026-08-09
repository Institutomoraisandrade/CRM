"""Utilidades compartilhadas."""

from __future__ import annotations

import unicodedata
from datetime import date, datetime, tzinfo

FORMATOS_DATA = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%Y/%m/%d")


def sem_acento(texto: str) -> str:
    normalizado = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in normalizado if not unicodedata.combining(c))


def chave(texto: str) -> str:
    """Normaliza um cabeçalho de planilha para comparação tolerante."""
    return " ".join(sem_acento(texto).strip().lower().split())


def ler_data(bruto: str | date | datetime | None) -> date | None:
    """Converte texto de planilha em ``date``.

    Aceita os formatos usuais de exportação brasileira e ISO. Devolve
    ``None`` para célula vazia; levanta ``ValueError`` para texto inválido,
    para que a linha problemática seja reportada em vez de silenciada.
    """
    if bruto is None:
        return None
    if isinstance(bruto, datetime):
        return bruto.date()
    if isinstance(bruto, date):
        return bruto
    texto = str(bruto).strip()
    if not texto:
        return None
    # Exportações às vezes trazem data e hora na mesma célula.
    texto = texto.split(" ")[0].split("T")[0]
    for formato in FORMATOS_DATA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    raise ValueError(f"data em formato não reconhecido: {bruto!r}")


def garantir_fuso(momento: datetime, fuso: tzinfo) -> datetime:
    """Anexa um fuso a datas ingênuas.

    Eventos gravados à mão em arquivo costumam vir sem offset; compará-los
    com datas cientes do fuso levanta ``TypeError``.
    """
    if momento.tzinfo is None:
        return momento.replace(tzinfo=fuso)
    return momento


def so_digitos(texto: str | None) -> str | None:
    if not texto:
        return None
    digitos = "".join(c for c in str(texto) if c.isdigit())
    return digitos or None
