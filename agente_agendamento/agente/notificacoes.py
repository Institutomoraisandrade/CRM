"""Fila de notificações.

O envio pelo WhatsApp fica **engatilhado, não disparado**: as mensagens
são montadas e gravadas em arquivo, prontas para um provedor de API ser
plugado depois. Nada sai da máquina do profissional.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

from .modelos import Agendamento, Alerta, Paciente, SituacaoAgendamento
from .regras import alertas_do_paciente, etiqueta_vigencia


@dataclass
class Notificacao:
    tipo: str
    paciente: str
    canal: str
    destino: str | None
    mensagem: str
    data_referencia: str
    enviado: bool = False
    metadados: dict = field(default_factory=dict)


def _mensagem_agendamento(agendamento: Agendamento) -> str:
    inicio = agendamento.inicio
    assert inicio is not None
    return (
        f"Olá, {agendamento.paciente.nome.split()[0]}! Seu retorno ficou marcado para "
        f"{inicio:%d/%m/%Y} às {inicio:%H:%M}. Qualquer imprevisto, me avise por aqui."
    )


def montar_notificacoes(
    pacientes: list[Paciente],
    agendamentos: list[Agendamento],
    hoje: date | None = None,
) -> list[Notificacao]:
    hoje = hoje or date.today()
    fila: list[Notificacao] = []

    for paciente in pacientes:
        for alerta in alertas_do_paciente(paciente, hoje):
            for destinatario in alerta.destinatarios:
                canal = "sistema" if destinatario == "profissional" else "whatsapp"
                destino = None if destinatario == "profissional" else paciente.whatsapp
                fila.append(
                    Notificacao(
                        tipo=alerta.tipo.value,
                        paciente=paciente.nome,
                        canal=canal,
                        destino=destino,
                        mensagem=alerta.mensagem,
                        data_referencia=alerta.data_referencia.isoformat(),
                        metadados={
                            "destinatario": destinatario,
                            "etiqueta": etiqueta_vigencia(paciente, hoje),
                            "plano": paciente.plano.nome,
                        },
                    )
                )

    for agendamento in agendamentos:
        if agendamento.inicio is None:
            continue
        if agendamento.situacao not in (
            SituacaoAgendamento.AGENDAVEL,
            SituacaoAgendamento.ATRASADO,
        ):
            continue
        fila.append(
            Notificacao(
                tipo="retorno_marcado",
                paciente=agendamento.paciente.nome,
                canal="whatsapp",
                destino=agendamento.paciente.whatsapp,
                mensagem=_mensagem_agendamento(agendamento),
                data_referencia=agendamento.inicio.date().isoformat(),
                metadados={
                    "destinatario": "paciente",
                    "inicio": agendamento.inicio.isoformat(),
                    "situacao": agendamento.situacao.value,
                },
            )
        )

    return fila


def gravar(fila: list[Notificacao], caminho: str | Path) -> Path:
    destino = Path(caminho).expanduser()
    destino.parent.mkdir(parents=True, exist_ok=True)
    conteudo = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "total": len(fila),
        "notificacoes": [asdict(n) for n in fila],
    }
    destino.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def alertas_pendentes(pacientes: list[Paciente], hoje: date) -> list[Alerta]:
    pendentes: list[Alerta] = []
    for paciente in pacientes:
        pendentes.extend(alertas_do_paciente(paciente, hoje))
    return pendentes
