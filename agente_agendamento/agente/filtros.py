"""Seleção de quais pacientes entram no relatório."""

from __future__ import annotations

from .modelos import Paciente, StatusPaciente
from .util import chave

# As etiquetas do LiveClin seguem o padrão "Ativos - <Profissional>".
PREFIXO_PROFISSIONAL = "ativos -"

SEM_PROFISSIONAL = "Sem profissional"


def tem_etiqueta(paciente: Paciente, etiqueta: str) -> bool:
    """Compara etiquetas ignorando acento, caixa e espaço sobrando."""
    alvo = chave(etiqueta)
    if not alvo:
        return True
    return any(chave(e) == alvo for e in paciente.etiquetas)


def tem_alguma_etiqueta(paciente: Paciente, etiquetas: list[str]) -> bool:
    if not etiquetas:
        return True
    return any(tem_etiqueta(paciente, e) for e in etiquetas)


def profissional_de(paciente: Paciente) -> str:
    """Extrai o nome do profissional da etiqueta "Ativos - <Nome>".

    Devolve o nome como está escrito na planilha, para o relatório poder
    separar os pacientes de cada um.
    """
    for etiqueta in paciente.etiquetas:
        normalizada = chave(etiqueta)
        if normalizada.startswith(PREFIXO_PROFISSIONAL):
            nome = etiqueta.split("-", 1)[1].strip()
            if nome:
                return nome
    return SEM_PROFISSIONAL


def aplicar(
    pacientes: list[Paciente],
    etiquetas: list[str] | str | None = None,
    somente_ativos: bool = True,
) -> list[Paciente]:
    alvos = [etiquetas] if isinstance(etiquetas, str) else list(etiquetas or [])
    alvos = [e for e in alvos if e and e.strip()]

    selecionados = pacientes
    if somente_ativos:
        selecionados = [p for p in selecionados if p.status is StatusPaciente.ATIVO]
    if alvos:
        selecionados = [p for p in selecionados if tem_alguma_etiqueta(p, alvos)]
    return selecionados


def descrever(etiquetas: list[str] | str | None, somente_ativos: bool) -> str:
    alvos = [etiquetas] if isinstance(etiquetas, str) else list(etiquetas or [])
    alvos = [e for e in alvos if e and e.strip()]
    partes = []
    if somente_ativos:
        partes.append("ativos")
    if alvos:
        partes.append(" + ".join(alvos))
    return " · ".join(partes)
