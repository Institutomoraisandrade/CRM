"""Catálogo de planos de acompanhamento.

As durações seguem os tipos usados no LiveClin: mensal, trimestral,
semestral e anual (30/90/180/360 dias).
"""

from __future__ import annotations

import re

from .modelos import Plano
from .util import sem_acento

CATALOGO_PADRAO: dict[str, Plano] = {
    "mensal": Plano("mensal", 30),
    "trimestral": Plano("trimestral", 90),
    "semestral": Plano("semestral", 180),
    "anual": Plano("anual", 360),
    # Plano de parceria: mesma duração do trimestral, valor zerado.
    "parceria": Plano("parceria", 90),
}

# Formas alternativas de escrever o mesmo plano numa planilha exportada.
_APELIDOS = {
    "1 mes": "mensal",
    "1 mês": "mensal",
    "30": "mensal",
    "30 dias": "mensal",
    "mensal": "mensal",
    "3 meses": "trimestral",
    "90": "trimestral",
    "90 dias": "trimestral",
    "trimestral": "trimestral",
    "6 meses": "semestral",
    "180": "semestral",
    "180 dias": "semestral",
    "semestral": "semestral",
    "12 meses": "anual",
    "1 ano": "anual",
    "360": "anual",
    "360 dias": "anual",
    "365": "anual",
    "365 dias": "anual",
    "anual": "anual",
}


def normalizar_nome(bruto: str) -> str:
    return " ".join(sem_acento(bruto).strip().lower().split())


# O LiveClin exporta o plano junto do serviço e da modalidade, como em
# "Dieta (3 Meses) - Presencial" ou "Treino (1 Mes) - Online".
_MESES = re.compile(r"(\d{1,2})\s*m[eê]s(?:es)?", re.IGNORECASE)

# Quantos meses correspondem a cada plano do catálogo padrão.
_POR_MESES = {1: "mensal", 3: "trimestral", 6: "semestral", 12: "anual"}


def _plano_por_meses(meses: int, catalogo: dict[str, Plano]) -> Plano | None:
    canonico = _POR_MESES.get(meses)
    if canonico and canonico in catalogo:
        return catalogo[canonico]
    if meses <= 0:
        return None
    # Duração fora do catálogo: monta um plano sob medida em vez de
    # descartar a linha.
    return Plano(f"{meses} meses", meses * 30)


def resolver_plano(bruto: str, catalogo: dict[str, Plano] | None = None) -> Plano | None:
    """Encontra o plano correspondente ao texto vindo da planilha.

    Aceita tanto o nome puro ("Trimestral") quanto o formato completo da
    exportação ("Dieta (3 Meses) - Presencial"). Retorna ``None`` quando
    não dá para deduzir a duração, para que a linha seja reportada em vez
    de virar um palpite.
    """
    catalogo = catalogo if catalogo is not None else CATALOGO_PADRAO
    nome = normalizar_nome(bruto)
    if not nome:
        return None
    if nome in catalogo:
        return catalogo[nome]
    canonico = _APELIDOS.get(nome)
    if canonico and canonico in catalogo:
        return catalogo[canonico]

    # Procura um nome de plano conhecido dentro do texto completo.
    for chave_catalogo, plano in catalogo.items():
        if chave_catalogo and chave_catalogo in nome:
            return plano

    encontrado = _MESES.search(nome)
    if encontrado:
        return _plano_por_meses(int(encontrado.group(1)), catalogo)

    return None


def plano_por_duracao(dias: int, catalogo: dict[str, Plano] | None = None) -> Plano:
    """Monta o plano a partir da duração explícita da planilha.

    A coluna "Duração (dias)" é mais confiável que o texto do plano, então
    quando ela existe é ela que manda.
    """
    catalogo = catalogo if catalogo is not None else CATALOGO_PADRAO
    for plano in catalogo.values():
        if plano.duracao_dias == dias:
            return plano
    return Plano(f"{dias} dias", dias)


def catalogo_de_config(planos_config: dict[str, int] | None) -> dict[str, Plano]:
    """Monta o catálogo a partir da configuração do usuário."""
    if not planos_config:
        return dict(CATALOGO_PADRAO)
    return {
        normalizar_nome(nome): Plano(normalizar_nome(nome), int(dias))
        for nome, dias in planos_config.items()
    }
