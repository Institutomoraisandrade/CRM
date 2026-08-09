"""Leitura das avaliações físicas exportadas do WebDiet.

Cada avaliação física registrada no WebDiet corresponde a uma consulta
realizada. O arquivo esperado é a exportação de avaliações, com pelo
menos o nome do paciente e a data.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from ..util import chave, ler_data
from .base import ErroDeFonte
from .planilha import Planilha, PlanilhaArquivo

# Colunas que trazem UMA data por paciente (a mais recente), e não o
# histórico de avaliações. Com elas dá para saber quando foi o último
# contato, mas não quantas consultas aconteceram.
COLUNAS_DE_SNAPSHOT = {
    "modificado em", "modificada em", "ultima modificacao", "criado em",
}

APELIDOS_COLUNA: dict[str, tuple[str, ...]] = {
    "paciente": (
        "paciente",
        "nome",
        "nome do paciente",
        "cliente",
        "nome completo",
    ),
    "data": (
        "data",
        "data da avaliacao",
        "data avaliacao",
        "data de avaliacao",
        "realizada em",
        "data da consulta",
        # Exportação de pacientes do WebDiet: última alteração da dieta.
        "modificado em",
        "modificada em",
        "ultima modificacao",
        "criado em",
    ),
}


@dataclass(frozen=True)
class Avaliacao:
    """Uma avaliação física, ou seja, uma consulta realizada."""

    paciente: str
    data: date


class FonteWebDiet:
    """Lê avaliações de qualquer planilha do WebDiet — arquivo ou Sheets."""

    def __init__(
        self, planilha: Planilha, colunas: dict[str, str] | None = None
    ) -> None:
        self.planilha = planilha
        self.colunas_config = {campo: chave(col) for campo, col in (colunas or {}).items()}
        self._avisos: list[str] = []
        self.historico = True
        self.coluna_de_data: str | None = None

    @property
    def avisos(self) -> list[str]:
        return self._avisos

    def _mapear_cabecalho(self, cabecalhos) -> dict[str, str]:
        disponiveis = {chave(c): c for c in cabecalhos if c}
        mapa: dict[str, str] = {}
        for campo, apelidos in APELIDOS_COLUNA.items():
            configurado = self.colunas_config.get(campo)
            if configurado and configurado in disponiveis:
                mapa[campo] = disponiveis[configurado]
                continue
            for apelido in apelidos:
                if apelido in disponiveis:
                    mapa[campo] = disponiveis[apelido]
                    break
        return mapa

    def carregar(self) -> list[Avaliacao]:
        linhas = self.planilha.linhas()
        if not linhas:
            raise ErroDeFonte(f"a exportação {self.planilha.descricao} está vazia.")

        mapa = self._mapear_cabecalho(linhas[0].keys())
        faltando = [c for c in ("paciente", "data") if c not in mapa]
        if faltando:
            raise ErroDeFonte(
                "não encontrei as colunas "
                + ", ".join(faltando)
                + f" em {self.planilha.descricao}. Colunas lidas: "
                + ", ".join(str(c) for c in linhas[0].keys())
                + ". Configure os nomes reais em [webdiet.colunas]."
            )

        self.coluna_de_data = mapa["data"]
        self.historico = chave(self.coluna_de_data) not in COLUNAS_DE_SNAPSHOT

        hoje = date.today()
        avaliacoes: list[Avaliacao] = []
        for numero, linha in enumerate(linhas, start=2):
            nome = linha.get(mapa["paciente"])
            nome = str(nome).strip() if nome is not None else ""
            if not nome:
                continue
            bruto = linha.get(mapa["data"])
            try:
                quando = ler_data(str(bruto).strip() if bruto is not None else None)
            except ValueError as erro:
                self._avisos.append(f"linha {numero} ignorada: {erro}")
                continue
            if quando is None:
                self._avisos.append(
                    f"linha {numero} ignorada: avaliação de {nome} está sem data"
                )
                continue
            if quando > hoje:
                self._avisos.append(
                    f"linha {numero} ignorada: avaliação de {nome} está no futuro "
                    f"({quando:%d/%m/%Y})"
                )
                continue
            avaliacoes.append(Avaliacao(paciente=nome, data=quando))

        return sorted(avaliacoes, key=lambda a: (a.paciente, a.data))


def FonteWebDietCSV(
    caminho: str | Path, colunas: dict[str, str] | None = None
) -> FonteWebDiet:
    """Atalho para ler o WebDiet de um arquivo em disco."""
    return FonteWebDiet(PlanilhaArquivo(caminho), colunas)
