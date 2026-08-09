"""Seleção de quais pacientes entram no relatório."""

from __future__ import annotations

from .modelos import Paciente, StatusPaciente
from .nomes import casar
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


def separar_excluidos(
    pacientes: list[Paciente], nomes: list[str] | None
) -> tuple[list[Paciente], list[tuple[Paciente, str]]]:
    """Tira da lista os pacientes cujos nomes foram informados.

    Serve enquanto a etiqueta do profissional não existe na exportação:
    dá para remover à mão quem é de outro profissional. Usa o mesmo
    casamento tolerante do resto do agente, então "Maria Santos" alcança
    "Maria S." — e, pelo mesmo motivo, o que saiu é sempre reportado, para
    você conferir que ninguém foi removido por engano.
    """
    alvos = [n for n in (nomes or []) if n and n.strip()]
    if not alvos:
        return list(pacientes), []

    disponiveis = [p.nome for p in pacientes]
    remover: dict[str, str] = {}
    for alvo in alvos:
        resultado = casar(alvo, disponiveis)
        if resultado.encontrou:
            remover[resultado.escolhido] = alvo

    mantidos = [p for p in pacientes if p.nome not in remover]
    excluidos = [(p, remover[p.nome]) for p in pacientes if p.nome in remover]
    return mantidos, excluidos


def aplicar(
    pacientes: list[Paciente],
    etiquetas: list[str] | str | None = None,
    somente_ativos: bool = True,
    excluir: list[str] | None = None,
) -> list[Paciente]:
    alvos = [etiquetas] if isinstance(etiquetas, str) else list(etiquetas or [])
    alvos = [e for e in alvos if e and e.strip()]

    selecionados = pacientes
    if somente_ativos:
        selecionados = [p for p in selecionados if p.status is StatusPaciente.ATIVO]
    if alvos:
        selecionados = [p for p in selecionados if tem_alguma_etiqueta(p, alvos)]
    if excluir:
        selecionados, _ = separar_excluidos(selecionados, excluir)
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
