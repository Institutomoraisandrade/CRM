"""Quais etiquetas cada paciente deve ter no BotConversa.

No BotConversa a etiqueta é o gatilho: `ativo-emagrec` dispara a
sequência de emagrecimento, `finalizado-*` dispara a de reativação. O
agente não escreve mensagem nenhuma — ele só mantém a etiqueta contando
a verdade, a partir do plano no LiveClin.

Quem manda o quê continua sendo decisão dos fluxos do BotConversa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .modelos import Paciente, StatusPaciente
from .regras import AVISO_VENCIMENTO_DIAS, INTERVALO_MAXIMO_DIAS
from .util import chave

# Etiqueta do LiveClin -> nicho usado nos fluxos do BotConversa.
NICHOS_PADRAO: dict[str, str] = {
    "emagrecimento": "emagrec",
    "emagrecer": "emagrec",
    "hipertrofia": "hiper",
    "hipertrofa": "hiper",
    "performance": "perf",
    "esporte": "perf",
    "esportes": "perf",
    "esportiva": "perf",
}

MESES_MAXIMO = 12

# Etiqueta extra, fora da taxonomia de nicho, para o aviso de renovação.
ETIQUETA_VENCENDO = "vence-7dias"


def nicho_de(paciente: Paciente, mapa: dict[str, str] | None = None) -> str | None:
    """Descobre o nicho a partir das etiquetas do LiveClin."""
    mapa = mapa if mapa is not None else NICHOS_PADRAO
    normalizado = {chave(k): v for k, v in mapa.items()}
    for etiqueta in paciente.etiquetas:
        nicho = normalizado.get(chave(etiqueta))
        if nicho:
            return nicho
    return None


def mes_do_acompanhamento(paciente: Paciente, hoje: date) -> int:
    """Em que mês do acompanhamento o paciente está, começando em 1."""
    if hoje < paciente.plano_inicio:
        return 1
    referencia = min(hoje, paciente.plano_fim)
    decorridos = (referencia - paciente.plano_inicio).days
    return max(1, min(MESES_MAXIMO, decorridos // INTERVALO_MAXIMO_DIAS + 1))


@dataclass
class PlanoDeEtiquetas:
    paciente: Paciente
    etiquetas: list[str] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)

    @property
    def receberia_mensagem(self) -> bool:
        """Se alguma etiqueta de sequência foi atribuída."""
        return any(
            e.startswith("ativo-") or e.startswith("finalizado-") for e in self.etiquetas
        )


def desejadas(
    paciente: Paciente,
    hoje: date | None = None,
    mapa_nichos: dict[str, str] | None = None,
) -> PlanoDeEtiquetas:
    """Etiquetas que este paciente deveria ter hoje no BotConversa."""
    hoje = hoje or date.today()
    plano = PlanoDeEtiquetas(paciente=paciente)

    nicho = nicho_de(paciente, mapa_nichos)
    if nicho is None:
        plano.observacoes.append(
            "sem etiqueta de nicho no LiveClin (emagrecimento, hipertrofia ou "
            "performance) — não dá para escolher a sequência"
        )
        return plano

    if paciente.status is StatusPaciente.PAUSADO:
        # Paciente pausado não pode cair na régua de mensagens.
        plano.observacoes.append(
            "paciente pausado — fica sem etiqueta de sequência para não receber disparo"
        )
        return plano

    vencido = paciente.plano_fim < hoje
    if paciente.status is StatusPaciente.INATIVO or vencido:
        plano.etiquetas.append(f"finalizado-{nicho}")
        if vencido and paciente.status is StatusPaciente.ATIVO:
            plano.observacoes.append(
                f"plano venceu em {paciente.plano_fim:%d/%m/%Y}, mas o LiveClin "
                "ainda marca como ativo — tratado como finalizado"
            )
        return plano

    plano.etiquetas.append(f"ativo-{nicho}")
    plano.etiquetas.append(f"mes-{mes_do_acompanhamento(paciente, hoje)}")

    restantes = paciente.dias_para_vencer_em(hoje)
    if 0 <= restantes <= AVISO_VENCIMENTO_DIAS:
        plano.etiquetas.append(ETIQUETA_VENCENDO)

    return plano


def para_todos(
    pacientes: list[Paciente],
    hoje: date | None = None,
    mapa_nichos: dict[str, str] | None = None,
) -> list[PlanoDeEtiquetas]:
    hoje = hoje or date.today()
    return [desejadas(p, hoje, mapa_nichos) for p in pacientes]
