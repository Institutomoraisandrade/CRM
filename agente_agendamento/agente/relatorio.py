"""Montagem do relatório diário enviado por e-mail."""

from __future__ import annotations

from datetime import date
from html import escape

from .modelos import (
    Agendamento,
    Alerta,
    Paciente,
    SituacaoAgendamento,
    StatusPaciente,
    TipoAlerta,
)
from .regras import INTERVALO_MAXIMO_DIAS, data_limite_retorno, etiqueta_vigencia

# Ordem de exibição: o que exige ação primeiro.
PRIORIDADE_ALERTA = {
    TipoAlerta.CONSULTA_ATRASADA: 0,
    TipoAlerta.PLANO_VENCIDO: 1,
    TipoAlerta.PLANO_VENCENDO: 2,
    TipoAlerta.RETORNO_30_DIAS: 3,
    TipoAlerta.CHECKIN_15_DIAS: 4,
}

ROTULO_ALERTA = {
    TipoAlerta.CONSULTA_ATRASADA: "Passou dos 30 dias",
    TipoAlerta.PLANO_VENCIDO: "Plano vencido",
    TipoAlerta.PLANO_VENCENDO: "Plano vencendo",
    TipoAlerta.RETORNO_30_DIAS: "Último dia do prazo",
    TipoAlerta.CHECKIN_15_DIAS: "Check-in de 15 dias",
}

ROTULO_SITUACAO = {
    SituacaoAgendamento.AGENDAVEL: "a marcar",
    SituacaoAgendamento.ATRASADO: "atrasado",
    SituacaoAgendamento.JA_AGENDADO: "já marcado",
    SituacaoAgendamento.SEM_VAGA: "sem vaga",
    SituacaoAgendamento.PLANO_VENCIDO: "plano vencido",
}

COR_SITUACAO = {
    SituacaoAgendamento.AGENDAVEL: "#1a7f4b",
    SituacaoAgendamento.ATRASADO: "#b3261e",
    SituacaoAgendamento.JA_AGENDADO: "#5f6368",
    SituacaoAgendamento.SEM_VAGA: "#a15c00",
    SituacaoAgendamento.PLANO_VENCIDO: "#b3261e",
}


class Relatorio:
    def __init__(
        self,
        pacientes: list[Paciente],
        agendamentos: list[Agendamento],
        alertas: list[Alerta],
        hoje: date | None = None,
    ) -> None:
        self.hoje = hoje or date.today()
        self.pacientes = pacientes
        self.agendamentos = agendamentos
        self.alertas = sorted(
            alertas,
            key=lambda a: (PRIORIDADE_ALERTA.get(a.tipo, 9), a.paciente.nome),
        )
        self.ativos = [p for p in pacientes if p.status is StatusPaciente.ATIVO]

    # -- números do topo -------------------------------------------------

    @property
    def marcados(self) -> list[Agendamento]:
        return [
            a
            for a in self.agendamentos
            if a.situacao in (SituacaoAgendamento.AGENDAVEL, SituacaoAgendamento.ATRASADO)
        ]

    @property
    def pendencias(self) -> list[Agendamento]:
        return [
            a
            for a in self.agendamentos
            if a.situacao in (SituacaoAgendamento.SEM_VAGA, SituacaoAgendamento.PLANO_VENCIDO)
        ]

    @property
    def assunto(self) -> str:
        partes = [f"Agenda {self.hoje:%d/%m}"]
        if self.marcados:
            partes.append(f"{len(self.marcados)} retorno(s)")
        if self.alertas:
            partes.append(f"{len(self.alertas)} alerta(s)")
        if self.pendencias:
            partes.append(f"{len(self.pendencias)} pendência(s)")
        if len(partes) == 1:
            partes.append("nada pendente")
        return " — ".join([partes[0], ", ".join(partes[1:])])

    # -- versão em texto puro --------------------------------------------

    def texto(self) -> str:
        linhas = [
            f"Relatório de agendamento — {self.hoje:%d/%m/%Y}",
            "",
            f"Pacientes ativos: {len(self.ativos)}",
            f"Retornos a marcar: {len(self.marcados)}",
            f"Alertas: {len(self.alertas)}",
            f"Pendências: {len(self.pendencias)}",
        ]

        if self.alertas:
            linhas += ["", "ALERTAS", "-" * 40]
            for alerta in self.alertas:
                rotulo = ROTULO_ALERTA.get(alerta.tipo, alerta.tipo.value)
                linhas.append(f"[{rotulo}] {alerta.mensagem}")

        if self.marcados:
            linhas += ["", f"RETORNOS (limite de {INTERVALO_MAXIMO_DIAS} dias)", "-" * 40]
            for item in sorted(self.marcados, key=lambda a: a.inicio):
                linhas.append(
                    f"{item.inicio:%d/%m/%Y %H:%M}  {item.paciente.nome}"
                    f"  (limite {item.limite:%d/%m/%Y}) — {item.motivo}"
                )

        if self.pendencias:
            linhas += ["", "PRECISAM DE DECISÃO SUA", "-" * 40]
            for item in self.pendencias:
                rotulo = ROTULO_SITUACAO.get(item.situacao, item.situacao.value)
                linhas.append(f"[{rotulo}] {item.paciente.nome} — {item.motivo}")

        linhas += [
            "",
            "-" * 40,
            "Enviado pelo agente de agendamento. Nada foi enviado aos pacientes.",
        ]
        return "\n".join(linhas)

    # -- versão HTML ------------------------------------------------------

    def html(self) -> str:
        blocos = [
            self._cabecalho(),
            self._resumo(),
            self._bloco_alertas(),
            self._bloco_retornos(),
            self._bloco_pendencias(),
            self._bloco_vigencias(),
            self._rodape(),
        ]
        corpo = "\n".join(b for b in blocos if b)
        return (
            '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,'
            'sans-serif;max-width:640px;margin:0 auto;padding:16px;color:#1f1f1f;'
            'line-height:1.5;">' + corpo + "</div>"
        )

    def _cabecalho(self) -> str:
        return (
            '<h1 style="font-size:20px;margin:0 0 4px;">Relatório de agendamento</h1>'
            f'<p style="margin:0 0 20px;color:#5f6368;font-size:14px;">'
            f"{self.hoje:%d/%m/%Y}</p>"
        )

    def _resumo(self) -> str:
        cartoes = [
            ("Pacientes ativos", len(self.ativos), "#1f1f1f"),
            ("Retornos a marcar", len(self.marcados), "#1a7f4b"),
            ("Alertas", len(self.alertas), "#a15c00" if self.alertas else "#5f6368"),
            ("Pendências", len(self.pendencias), "#b3261e" if self.pendencias else "#5f6368"),
        ]
        celulas = "".join(
            '<td style="padding:10px 12px;border:1px solid #e0e0e0;border-radius:6px;">'
            f'<div style="font-size:22px;font-weight:600;color:{cor};">{valor}</div>'
            f'<div style="font-size:12px;color:#5f6368;">{escape(titulo)}</div>'
            "</td>"
            for titulo, valor, cor in cartoes
        )
        return (
            '<table role="presentation" style="border-collapse:separate;border-spacing:6px;'
            f'width:100%;margin-bottom:24px;"><tr>{celulas}</tr></table>'
        )

    @staticmethod
    def _titulo_secao(texto: str) -> str:
        return (
            '<h2 style="font-size:15px;margin:24px 0 8px;padding-bottom:6px;'
            f'border-bottom:1px solid #e0e0e0;">{escape(texto)}</h2>'
        )

    def _bloco_alertas(self) -> str:
        if not self.alertas:
            return ""
        itens = []
        for alerta in self.alertas:
            rotulo = ROTULO_ALERTA.get(alerta.tipo, alerta.tipo.value)
            urgente = alerta.tipo in (
                TipoAlerta.CONSULTA_ATRASADA,
                TipoAlerta.PLANO_VENCIDO,
            )
            cor = "#b3261e" if urgente else "#a15c00"
            itens.append(
                f'<li style="margin-bottom:10px;"><span style="display:inline-block;'
                f"font-size:11px;font-weight:600;color:{cor};border:1px solid {cor};"
                'border-radius:4px;padding:1px 6px;margin-right:6px;">'
                f"{escape(rotulo)}</span>{escape(alerta.mensagem)}</li>"
            )
        return (
            self._titulo_secao("Alertas de hoje")
            + '<ul style="margin:0;padding-left:18px;font-size:14px;">'
            + "".join(itens)
            + "</ul>"
        )

    def _bloco_retornos(self) -> str:
        if not self.marcados:
            return ""
        linhas = []
        for item in sorted(self.marcados, key=lambda a: a.inicio):
            cor = COR_SITUACAO.get(item.situacao, "#1f1f1f")
            rotulo = ROTULO_SITUACAO.get(item.situacao, item.situacao.value)
            linhas.append(
                '<tr><td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:14px;">'
                f"<strong>{escape(item.paciente.nome)}</strong><br>"
                f'<span style="color:#5f6368;font-size:12px;">{escape(item.motivo)}</span></td>'
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:14px;'
                'white-space:nowrap;">'
                f"{item.inicio:%d/%m %H:%M}</td>"
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:12px;'
                'white-space:nowrap;">'
                f"{item.limite:%d/%m}</td>"
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:12px;'
                f'color:{cor};white-space:nowrap;">{escape(rotulo)}</td></tr>'
            )
        return (
            self._titulo_secao(f"Retornos dentro do limite de {INTERVALO_MAXIMO_DIAS} dias")
            + '<table role="presentation" style="border-collapse:collapse;width:100%;">'
            '<tr><th align="left" style="padding:6px;font-size:11px;color:#5f6368;'
            'text-transform:uppercase;">Paciente</th>'
            '<th align="left" style="padding:6px;font-size:11px;color:#5f6368;'
            'text-transform:uppercase;">Retorno</th>'
            '<th align="left" style="padding:6px;font-size:11px;color:#5f6368;'
            'text-transform:uppercase;">Limite</th>'
            '<th align="left" style="padding:6px;font-size:11px;color:#5f6368;'
            'text-transform:uppercase;">Situação</th></tr>'
            + "".join(linhas)
            + "</table>"
        )

    def _bloco_pendencias(self) -> str:
        if not self.pendencias:
            return ""
        itens = "".join(
            f'<li style="margin-bottom:8px;"><strong>{escape(item.paciente.nome)}</strong> — '
            f"{escape(item.motivo)}</li>"
            for item in self.pendencias
        )
        return (
            self._titulo_secao("Precisam de decisão sua")
            + f'<ul style="margin:0;padding-left:18px;font-size:14px;">{itens}</ul>'
        )

    def _bloco_vigencias(self) -> str:
        proximos = [
            p
            for p in self.ativos
            if 0 <= p.dias_para_vencer_em(self.hoje) <= 15
        ]
        if not proximos:
            return ""
        itens = "".join(
            f'<li style="margin-bottom:6px;"><strong>{escape(p.nome)}</strong> '
            f'<span style="color:#5f6368;">({escape(p.plano.nome)})</span> — '
            f"{escape(etiqueta_vigencia(p, self.hoje))}, até {p.plano_fim:%d/%m/%Y}</li>"
            for p in sorted(proximos, key=lambda p: p.plano_fim)
        )
        return (
            self._titulo_secao("Planos terminando nos próximos 15 dias")
            + f'<ul style="margin:0;padding-left:18px;font-size:14px;">{itens}</ul>'
        )

    def _rodape(self) -> str:
        return (
            '<p style="margin-top:28px;padding-top:12px;border-top:1px solid #e0e0e0;'
            'font-size:12px;color:#5f6368;">'
            "Enviado pelo agente de agendamento, da sua máquina. "
            "Nenhuma mensagem foi enviada aos pacientes.</p>"
        )


def montar(
    pacientes: list[Paciente],
    agendamentos: list[Agendamento],
    alertas: list[Alerta],
    hoje: date | None = None,
) -> Relatorio:
    return Relatorio(pacientes, agendamentos, alertas, hoje)
