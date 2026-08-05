"""Seleção de quais pacientes entram no relatório."""

from __future__ import annotations

from .modelos import Paciente, StatusPaciente
from .util import chave


def tem_etiqueta(paciente: Paciente, etiqueta: str) -> bool:
    """Compara etiquetas ignorando acento, caixa e espaço sobrando."""
    alvo = chave(etiqueta)
    if not alvo:
        return True
    return any(chave(e) == alvo for e in paciente.etiquetas)


def aplicar(
    pacientes: list[Paciente],
    etiqueta: str | None = None,
    somente_ativos: bool = True,
) -> list[Paciente]:
    selecionados = pacientes
    if somente_ativos:
        selecionados = [p for p in selecionados if p.status is StatusPaciente.ATIVO]
    if etiqueta:
        selecionados = [p for p in selecionados if tem_etiqueta(p, etiqueta)]
    return selecionados


def descrever(etiqueta: str | None, somente_ativos: bool) -> str:
    partes = []
    if somente_ativos:
        partes.append("ativos")
    if etiqueta:
        partes.append(f"etiqueta {etiqueta}")
    return " · ".join(partes)
