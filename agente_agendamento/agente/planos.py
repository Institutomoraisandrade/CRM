"""Catálogo de planos de acompanhamento.

As durações seguem os tipos usados no LiveClin: mensal, trimestral,
semestral e anual (30/90/180/360 dias).
"""

from __future__ import annotations

from .modelos import Plano

CATALOGO_PADRAO: dict[str, Plano] = {
    "mensal": Plano("mensal", 30),
    "trimestral": Plano("trimestral", 90),
    "semestral": Plano("semestral", 180),
    "anual": Plano("anual", 360),
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
    return " ".join(bruto.strip().lower().split())


def resolver_plano(bruto: str, catalogo: dict[str, Plano] | None = None) -> Plano | None:
    """Encontra o plano correspondente ao texto vindo da planilha.

    Retorna ``None`` quando o texto não corresponde a nenhum plano conhecido,
    para que o chamador decida entre ignorar a linha ou reportar o erro.
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
    return None


def catalogo_de_config(planos_config: dict[str, int] | None) -> dict[str, Plano]:
    """Monta o catálogo a partir da configuração do usuário."""
    if not planos_config:
        return dict(CATALOGO_PADRAO)
    return {
        normalizar_nome(nome): Plano(normalizar_nome(nome), int(dias))
        for nome, dias in planos_config.items()
    }
