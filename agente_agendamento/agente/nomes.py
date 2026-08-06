"""Casamento de nomes entre sistemas diferentes.

O mesmo paciente aparece escrito de formas diferentes no LiveClin e no
WebDiet — abreviação, acento faltando, erro de digitação. Este módulo
encontra o par certo e, principalmente, **se recusa a adivinhar** quando
há mais de um candidato plausível.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .util import sem_acento

# Acima disto, dois nomes são considerados a mesma pessoa.
LIMIAR_ACEITE = 0.86

# Se o segundo colocado estiver a menos disto do primeiro, o caso é
# ambíguo: preferimos não decidir a decidir errado.
MARGEM_MINIMA = 0.06

# Partículas que não ajudam a distinguir pessoas.
PARTICULAS = {"de", "da", "do", "das", "dos", "e"}


def normalizar(nome: str) -> str:
    """Reduz o nome à forma comparável: sem acento, sem pontuação, minúsculo."""
    limpo = sem_acento(nome).lower()
    limpo = "".join(c if c.isalnum() or c.isspace() else " " for c in limpo)
    return " ".join(limpo.split())


def tokens(nome: str) -> list[str]:
    return [t for t in normalizar(nome).split() if t not in PARTICULAS]


def _iniciais_compativeis(a: list[str], b: list[str]) -> bool:
    """Trata abreviação: "Ana C Souza" combina com "Ana Carolina Souza"."""
    if len(a) != len(b):
        return False
    for ta, tb in zip(a, b):
        if ta == tb:
            continue
        curto, longo = (ta, tb) if len(ta) < len(tb) else (tb, ta)
        if len(curto) == 1 and longo.startswith(curto):
            continue
        return False
    return True


# Teto aplicado quando um pedaço do nome não confere. Fica abaixo do
# limiar de aceite, então o par é recusado.
TETO_INCOMPATIVEL = 0.70

# A partir deste tamanho, o pedaço tolera dois erros de digitação.
TAMANHO_TOLERANTE = 8


def distancia(a: str, b: str) -> int:
    """Quantas edições transformam um texto no outro (Levenshtein).

    Distingue erro de digitação de nome diferente melhor que proporção de
    caracteres: "Oaiva"/"Paiva" custa 1 edição, "Alves"/"Sales" custa 2
    apesar de as duas duplas parecerem igualmente semelhantes.
    """
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(
                min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + (ca != cb))
            )
        anterior = atual
    return anterior[-1]


def _abreviacao(a: str, b: str) -> bool:
    """Um é começo do outro: Nathan/Nathaniel, Bea/Beatriz."""
    curto, longo = sorted((a, b), key=len)
    return len(curto) >= 4 and longo.startswith(curto)


def _pedacos_conferem(a: str, b: str) -> bool:
    """Decide se dois pedaços de nome são a mesma coisa escrita diferente."""
    if a == b or _abreviacao(a, b):
        return True
    dist = distancia(a, b)
    if dist <= 1:
        return True
    return dist <= 2 and min(len(a), len(b)) >= TAMANHO_TOLERANTE


def semelhanca(a: str, b: str) -> float:
    """Nota de 0 a 1 entre dois nomes."""
    na, nb = normalizar(a), normalizar(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0

    ta, tb = tokens(a), tokens(b)
    if ta and ta == tb:
        return 1.0
    if ta and sorted(ta) == sorted(tb):
        # Mesma pessoa com sobrenome trocado de lugar.
        return 0.97
    if _iniciais_compativeis(ta, tb):
        return 0.95

    direta = SequenceMatcher(None, na, nb).ratio()

    # Compara também token a token, para que um erro concentrado num
    # sobrenome não afunde o nome inteiro.
    if ta and tb and len(ta) == len(tb):
        if not all(_pedacos_conferem(x, y) for x, y in zip(ta, tb)):
            # Um dos pedaços é outro nome, não uma variação do mesmo.
            # Nome igual no começo não pode carregar sobrenome diferente.
            return min(direta, TETO_INCOMPATIVEL)
        notas = [SequenceMatcher(None, x, y).ratio() for x, y in zip(ta, tb)]
        por_token = sum(notas) / len(notas)
        return max(direta, por_token)

    return direta


@dataclass
class Correspondencia:
    consultado: str
    escolhido: str | None
    nota: float
    candidatos: list[tuple[str, float]]
    ambiguo: bool = False

    @property
    def encontrou(self) -> bool:
        return self.escolhido is not None

    @property
    def exato(self) -> bool:
        return self.nota >= 0.999

    def explicar(self) -> str:
        if self.ambiguo:
            nomes = ", ".join(f"{n} ({p:.0%})" for n, p in self.candidatos[:3])
            return (
                f"{self.consultado!r} ficou ambíguo entre: {nomes}. "
                "Confirme manualmente qual é o correto."
            )
        if not self.encontrou:
            if self.candidatos:
                nome, nota = self.candidatos[0]
                return (
                    f"{self.consultado!r} não bateu com ninguém "
                    f"(mais próximo: {nome}, {nota:.0%})"
                )
            return f"{self.consultado!r} não bateu com ninguém"
        if self.exato:
            return f"{self.consultado!r} = {self.escolhido!r}"
        return f"{self.consultado!r} ≈ {self.escolhido!r} ({self.nota:.0%})"


def casar(
    consultado: str,
    candidatos: list[str],
    limiar: float = LIMIAR_ACEITE,
    margem: float = MARGEM_MINIMA,
) -> Correspondencia:
    """Encontra, entre ``candidatos``, o nome que corresponde a ``consultado``.

    Devolve ``escolhido=None`` quando nada passa do limiar **ou** quando
    dois candidatos ficam empatados dentro da margem. Nesse segundo caso
    ``ambiguo`` fica ``True``: é um pedido de confirmação humana, não uma
    ausência de resultado.
    """
    notas = sorted(
        ((c, semelhanca(consultado, c)) for c in candidatos),
        key=lambda par: (-par[1], par[0]),
    )
    if not notas:
        return Correspondencia(consultado, None, 0.0, [])

    melhor, nota = notas[0]
    if nota < limiar:
        return Correspondencia(consultado, None, nota, notas[:5])

    # Nota máxima nunca é ambígua: é igualdade literal.
    if nota < 0.999 and len(notas) > 1:
        _, segunda = notas[1]
        if nota - segunda < margem:
            return Correspondencia(consultado, None, nota, notas[:5], ambiguo=True)

    return Correspondencia(consultado, melhor, nota, notas[:5])
