"""Montagem do relatório diário enviado por e-mail."""

from __future__ import annotations

from datetime import date
from html import escape

from .consultas import Cruzamento
from .filtros import profissional_de
from .modelos import (
    Agendamento,
    Alerta,
    Paciente,
    SituacaoAgendamento,
    StatusPaciente,
    TipoAlerta,
)
from .prioridade import ItemPrioridade, montar_fila
from .regras import INTERVALO_MAXIMO_DIAS, etiqueta_vigencia

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

VERMELHO = "#b3261e"
AMBAR = "#a15c00"
VERDE = "#1a7f4b"
CINZA = "#5f6368"


class Relatorio:
    def __init__(
        self,
        pacientes: list[Paciente],
        agendamentos: list[Agendamento],
        alertas: list[Alerta],
        hoje: date | None = None,
        cruzamento: Cruzamento | None = None,
        titulo_filtro: str = "",
    ) -> None:
        self.hoje = hoje or date.today()
        self.pacientes = pacientes
        self.agendamentos = agendamentos
        self.cruzamento = cruzamento
        self.titulo_filtro = titulo_filtro
        self.alertas = sorted(
            alertas,
            key=lambda a: (PRIORIDADE_ALERTA.get(a.tipo, 9), a.paciente.nome),
        )
        self.ativos = [p for p in pacientes if p.status is StatusPaciente.ATIVO]
        self.fila = montar_fila(agendamentos, cruzamento, self.hoje)

    # -- números do topo -------------------------------------------------

    @property
    def marcados(self) -> list[Agendamento]:
        return [
            a
            for a in self.agendamentos
            if a.situacao in (SituacaoAgendamento.AGENDAVEL, SituacaoAgendamento.ATRASADO)
        ]

    @property
    def urgentes_30_dias(self) -> list[ItemPrioridade]:
        """Quem já chegou ou passou dos 30 dias desde a última consulta.

        É o alarme do relatório: o prazo é para ser cumprido, não
        esticado, então esses casos aparecem antes de qualquer outra coisa.

        Só entra quem tem data de última consulta registrada. Sem ela o
        limite seria contado do início do plano, e um paciente antigo
        apareceria com centenas de dias de atraso que ninguém pode
        confirmar — alarme falso gasta a atenção que o alarme real precisa.
        """
        return [
            item
            for item in self.fila
            if item.paciente.ultima_consulta is not None
            and item.agendamento.limite is not None
            and item.agendamento.limite <= self.hoje
            and item.agendamento.situacao is not SituacaoAgendamento.PLANO_VENCIDO
        ]

    @property
    def sem_data_de_consulta(self) -> list[Paciente]:
        """Ativos cujo prazo de 30 dias não dá para aferir."""
        return [p for p in self.ativos if p.ultima_consulta is None]

    @property
    def por_profissional(self) -> dict[str, list[Paciente]]:
        agrupados: dict[str, list[Paciente]] = {}
        for paciente in self.ativos:
            agrupados.setdefault(profissional_de(paciente), []).append(paciente)
        return dict(sorted(agrupados.items()))

    @property
    def programados(self) -> list[Agendamento]:
        """Consultas com data definida, urgentes ou não."""
        return sorted(
            (a for a in self.agendamentos if a.inicio is not None),
            key=lambda a: a.inicio,
        )

    @property
    def pendencias(self) -> list[Agendamento]:
        return [
            a
            for a in self.agendamentos
            if a.situacao in (SituacaoAgendamento.SEM_VAGA, SituacaoAgendamento.PLANO_VENCIDO)
        ]

    @property
    def em_atraso_de_consulta(self) -> int:
        if not self.cruzamento:
            return 0
        return sum(
            1
            for p in self.ativos
            if (r := self.cruzamento.de(p)) and r.deficit > 0
        )

    @property
    def assunto(self) -> str:
        urgentes = self.urgentes_30_dias
        if urgentes:
            plural = "paciente" if len(urgentes) == 1 else "pacientes"
            return (
                f"🚨 {len(urgentes)} {plural} NO LIMITE DE {INTERVALO_MAXIMO_DIAS} DIAS "
                f"— agenda {self.hoje:%d/%m}"
            )
        if self.fila:
            return (
                f"Agenda {self.hoje:%d/%m} — "
                f"{len(self.fila)} paciente(s) para agendar"
            )
        return f"Agenda {self.hoje:%d/%m} — nada pendente"

    # -- versão em texto puro --------------------------------------------

    def texto(self) -> str:
        linhas = [f"Relatório de agendamento — {self.hoje:%d/%m/%Y}"]
        if self.titulo_filtro:
            linhas.append(self.titulo_filtro)

        urgentes = self.urgentes_30_dias
        if urgentes:
            plural = "PACIENTE" if len(urgentes) == 1 else "PACIENTES"
            linhas += [
                "",
                "!" * 52,
                f"🚨 {len(urgentes)} {plural} NO LIMITE DE "
                f"{INTERVALO_MAXIMO_DIAS} DIAS",
                "O prazo entre consultas não pode ser esticado. Agendar hoje.",
                "!" * 52,
            ]
            for item in urgentes:
                atraso = (self.hoje - item.agendamento.limite).days
                if atraso == 0:
                    selo = "HOJE É O LIMITE"
                else:
                    selo = f"+{atraso} dia" + ("s" if atraso > 1 else "")
                linhas.append(
                    f"  [{selo}] {item.paciente.nome} "
                    f"({profissional_de(item.paciente)} · {item.paciente.plano.nome})"
                )
                if item.paciente.ultima_consulta:
                    linhas.append(
                        f"        última consulta "
                        f"{item.paciente.ultima_consulta:%d/%m/%Y}, "
                        f"limite era {item.agendamento.limite:%d/%m/%Y}"
                    )
                if item.agendamento.inicio:
                    linhas.append(
                        f"        encaixe sugerido: "
                        f"{item.agendamento.inicio:%d/%m/%Y às %H:%M}"
                    )

        linhas += [
            "",
            f"Pacientes ativos: {len(self.ativos)}",
            f"Para agendar agora: {len(self.fila)}",
            f"Com consultas em atraso: {self.em_atraso_de_consulta}",
            f"Pendências: {len(self.pendencias)}",
        ]

        grupos = self.por_profissional
        if len(grupos) > 1:
            linhas.append("")
            linhas.append("Por profissional: " + ", ".join(
                f"{nome} ({len(pacientes)})" for nome, pacientes in grupos.items()
            ))

        if self.fila:
            linhas += ["", "=" * 52, "AGENDAR AGORA (prioridade)", "=" * 52]
            for posicao, item in enumerate(self.fila, start=1):
                linhas.append(
                    f"{posicao}. {item.paciente.nome} "
                    f"[{item.paciente.plano.nome}]{self._consultas_texto(item)}"
                )
                for motivo in item.motivos:
                    linhas.append(f"     - {motivo}")
                if item.agendamento.inicio:
                    linhas.append(
                        f"     sugestão: {item.agendamento.inicio:%d/%m/%Y às %H:%M}"
                    )

        if self.programados:
            linhas += [
                "",
                f"AGENDA — RETORNOS (limite de {INTERVALO_MAXIMO_DIAS} dias)",
                "-" * 52,
            ]
            for item in self.programados:
                rotulo = ROTULO_SITUACAO.get(item.situacao, item.situacao.value)
                limite = f"{item.limite:%d/%m}" if item.limite else "—"
                linhas.append(
                    f"{item.inicio:%d/%m/%Y %H:%M}  {item.paciente.nome:<26} "
                    f"limite {limite}  [{rotulo}]"
                )

        quadro = self._quadro_consultas()
        if quadro:
            linhas += ["", "CONSULTAS POR PACIENTE", "-" * 52] + quadro

        if self.alertas:
            linhas += ["", "ALERTAS", "-" * 52]
            for alerta in self.alertas:
                rotulo = ROTULO_ALERTA.get(alerta.tipo, alerta.tipo.value)
                linhas.append(f"[{rotulo}] {alerta.mensagem}")

        faltantes = self.sem_data_de_consulta
        if faltantes:
            linhas += [
                "",
                f"{len(faltantes)} paciente(s) SEM DATA DA ÚLTIMA CONSULTA — o limite",
                f"de {INTERVALO_MAXIMO_DIAS} dias não pode ser aferido para eles, então",
                "ficam fora do alarme. A data vem do WebDiet.",
            ]

        conferir = self._conferir()
        if conferir:
            linhas += ["", "CONFERIR MANUALMENTE", "-" * 52] + [
                f"- {c}" for c in conferir
            ]

        linhas += [
            "",
            "-" * 52,
            "Enviado pelo agente de agendamento. Nada foi enviado aos pacientes.",
        ]
        return "\n".join(linhas)

    def _consultas_texto(self, item: ItemPrioridade) -> str:
        if item.resumo is None or item.resumo.sem_dados:
            return ""
        return f" — {item.resumo.realizadas} de {item.resumo.previstas_total} consultas"

    def _quadro_consultas(self) -> list[str]:
        if not self.cruzamento:
            return []
        linhas = []
        for paciente in sorted(self.ativos, key=lambda p: p.nome):
            resumo = self.cruzamento.de(paciente)
            if resumo is None:
                continue
            if resumo.sem_dados:
                estado = "sem registro no WebDiet"
            elif resumo.deficit > 0:
                estado = f"faltam {resumo.deficit}"
            elif resumo.esgotadas:
                estado = "consultas esgotadas"
            else:
                estado = "em dia"
            linhas.append(
                f"{paciente.nome:<26} {profissional_de(paciente):<10} "
                f"{paciente.plano.nome:<12} "
                f"feitas {resumo.realizadas:>2} de {resumo.previstas_total:<3} "
                f"(previstas até hoje: {resumo.previstas_ate_hoje})  {estado}"
            )
        return linhas

    def _conferir(self) -> list[str]:
        if not self.cruzamento:
            return []
        itens = [c.explicar() for c in self.cruzamento.ambiguidades]
        itens += [
            f"{c.consultado!r} está no WebDiet mas não bateu com nenhum paciente ativo"
            for c in self.cruzamento.sem_paciente
        ]
        return itens

    # -- versão HTML ------------------------------------------------------

    def html(self) -> str:
        blocos = [
            self._cabecalho(),
            self._bloco_alarme(),
            self._resumo(),
            self._bloco_equipe(),
            self._bloco_prioridade(),
            self._bloco_programados(),
            self._bloco_quadro_consultas(),
            self._bloco_alertas(),
            self._bloco_sem_data(),
            self._bloco_conferir(),
            self._bloco_vigencias(),
            self._rodape(),
        ]
        corpo = "\n".join(b for b in blocos if b)
        return (
            '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,'
            'sans-serif;max-width:680px;margin:0 auto;padding:16px;color:#1f1f1f;'
            'line-height:1.5;">' + corpo + "</div>"
        )

    def _cabecalho(self) -> str:
        filtro = (
            f'<span style="color:{CINZA};"> · {escape(self.titulo_filtro)}</span>'
            if self.titulo_filtro
            else ""
        )
        return (
            '<h1 style="font-size:20px;margin:0 0 4px;">Relatório de agendamento</h1>'
            f'<p style="margin:0 0 20px;color:{CINZA};font-size:14px;">'
            f"{self.hoje:%d/%m/%Y}{filtro}</p>"
        )

    def _resumo(self) -> str:
        cartoes = [
            ("Pacientes ativos", len(self.ativos), "#1f1f1f"),
            ("Agendar agora", len(self.fila), VERMELHO if self.fila else CINZA),
            (
                "Consultas em atraso",
                self.em_atraso_de_consulta,
                AMBAR if self.em_atraso_de_consulta else CINZA,
            ),
            ("Pendências", len(self.pendencias), AMBAR if self.pendencias else CINZA),
        ]
        celulas = "".join(
            '<td style="padding:10px 12px;border:1px solid #e0e0e0;border-radius:6px;'
            'text-align:center;">'
            f'<div style="font-size:24px;font-weight:600;color:{cor};">{valor}</div>'
            f'<div style="font-size:12px;color:{CINZA};">{escape(titulo)}</div>'
            "</td>"
            for titulo, valor, cor in cartoes
        )
        return (
            '<table role="presentation" style="border-collapse:separate;border-spacing:6px;'
            f'width:100%;margin-bottom:24px;"><tr>{celulas}</tr></table>'
        )

    def _bloco_equipe(self) -> str:
        """Quantos pacientes de cada profissional entraram no relatório."""
        grupos = self.por_profissional
        if len(grupos) < 2:
            return ""
        celulas = "".join(
            '<td style="padding:8px 12px;border:1px solid #e0e0e0;border-radius:6px;">'
            f'<div style="font-size:13px;color:{CINZA};">{escape(nome)}</div>'
            f'<div style="font-size:18px;font-weight:600;">{len(pacientes)}'
            f'<span style="font-size:12px;font-weight:400;color:{CINZA};">'
            " pacientes</span></div></td>"
            for nome, pacientes in grupos.items()
        )
        return (
            self._titulo_secao("Pacientes por profissional")
            + '<table role="presentation" style="border-collapse:separate;'
            f'border-spacing:6px;"><tr>{celulas}</tr></table>'
        )

    @staticmethod
    def _titulo_secao(texto: str) -> str:
        return (
            '<h2 style="font-size:15px;margin:26px 0 8px;padding-bottom:6px;'
            f'border-bottom:1px solid #e0e0e0;">{escape(texto)}</h2>'
        )

    def _bloco_alarme(self) -> str:
        """Alarme dos 30 dias: o primeiro bloco, impossível de ignorar."""
        urgentes = self.urgentes_30_dias
        if not urgentes:
            return ""

        linhas = []
        for item in urgentes:
            limite = item.agendamento.limite
            atraso = (self.hoje - limite).days
            if atraso == 0:
                selo, cor_selo = "HOJE É O LIMITE", "#8a1109"
            else:
                selo, cor_selo = f"+{atraso} DIA{'S' if atraso > 1 else ''}", "#6b0d07"
            detalhes = [f"limite era {limite:%d/%m/%Y}"]
            if item.paciente.ultima_consulta:
                detalhes.insert(
                    0, f"última consulta {item.paciente.ultima_consulta:%d/%m/%Y}"
                )
            if item.agendamento.inicio:
                detalhes.append(
                    f"encaixe sugerido {item.agendamento.inicio:%d/%m/%Y às %H:%M}"
                )

            linhas.append(
                '<div style="background:#ffffff;border-radius:6px;padding:10px 12px;'
                'margin-bottom:8px;">'
                '<table role="presentation" style="width:100%;border-collapse:collapse;">'
                '<tr><td style="font-size:16px;font-weight:700;color:#8a1109;">'
                f"{escape(item.paciente.nome)}"
                '<span style="font-weight:400;font-size:13px;color:#7a4b46;"> · '
                f"{escape(profissional_de(item.paciente))} · "
                f"{escape(item.paciente.plano.nome)}</span></td>"
                '<td align="right" style="white-space:nowrap;"><span style="display:'
                f"inline-block;background:{cor_selo};color:#ffffff;font-size:12px;"
                'font-weight:700;border-radius:4px;padding:3px 8px;">'
                f"{escape(selo)}</span></td></tr></table>"
                '<div style="font-size:13px;color:#5c1a14;margin-top:4px;">'
                f"{escape(' · '.join(detalhes))}</div></div>"
            )

        plural = "PACIENTE" if len(urgentes) == 1 else "PACIENTES"
        return (
            '<div style="background:#b3261e;border-radius:10px;padding:16px;'
            'margin-bottom:20px;">'
            '<div style="font-size:22px;font-weight:800;color:#ffffff;'
            'letter-spacing:0.3px;margin-bottom:4px;">'
            f"🚨 {len(urgentes)} {plural} NO LIMITE DE {INTERVALO_MAXIMO_DIAS} DIAS</div>"
            '<div style="font-size:13px;color:#ffe0dc;margin-bottom:12px;">'
            "O prazo entre consultas não pode ser esticado. Agendar hoje.</div>"
            + "".join(linhas)
            + "</div>"
        )

    def _bloco_prioridade(self) -> str:
        """O destaque do e-mail: quem precisa ser agendado agora."""
        if not self.fila:
            return (
                f'<div style="border:1px solid #cde8d8;background:#f2fbf6;'
                f'border-radius:8px;padding:14px 16px;margin-bottom:8px;">'
                f'<strong style="color:{VERDE};">Ninguém precisa ser agendado hoje.</strong>'
                f'<div style="font-size:13px;color:{CINZA};margin-top:4px;">'
                "Todos os pacientes ativos estão dentro do limite de "
                f"{INTERVALO_MAXIMO_DIAS} dias.</div></div>"
            )

        cartoes = []
        for posicao, item in enumerate(self.fila, start=1):
            cor = VERMELHO if item.peso <= 2 else AMBAR
            consultas = ""
            if item.resumo is not None and not item.resumo.sem_dados:
                consultas = (
                    f'<span style="color:{CINZA};font-size:13px;"> · '
                    f"{item.resumo.realizadas} de {item.resumo.previstas_total} consultas"
                    "</span>"
                )
            motivos = "".join(
                f'<li style="margin-bottom:2px;">{escape(m)}</li>' for m in item.motivos
            )
            sugestao = ""
            if item.agendamento.inicio:
                sugestao = (
                    f'<div style="font-size:13px;color:{VERDE};margin-top:6px;">'
                    f"Sugestão: {item.agendamento.inicio:%d/%m/%Y às %H:%M}</div>"
                )
            cartoes.append(
                f'<div style="border-left:4px solid {cor};background:#fbfbfb;'
                'padding:12px 14px;margin-bottom:8px;border-radius:0 6px 6px 0;">'
                f'<div style="font-size:15px;font-weight:600;">{posicao}. '
                f"{escape(item.paciente.nome)}"
                f'<span style="font-weight:400;color:{CINZA};font-size:13px;"> · '
                f"{escape(profissional_de(item.paciente))} · "
                f"{escape(item.paciente.plano.nome)}</span>{consultas}</div>"
                f'<ul style="margin:6px 0 0;padding-left:18px;font-size:13px;'
                f'color:{cor};">{motivos}</ul>{sugestao}</div>'
            )

        return (
            '<div style="background:#fff4f2;border:1px solid #f3d3cd;border-radius:8px;'
            'padding:14px 16px;margin-bottom:8px;">'
            f'<div style="font-size:16px;font-weight:700;color:{VERMELHO};'
            'margin-bottom:10px;">'
            f"Agendar agora — {len(self.fila)} paciente(s)</div>"
            + "".join(cartoes)
            + "</div>"
        )

    def _bloco_programados(self) -> str:
        if not self.programados:
            return ""
        linhas = []
        for item in self.programados:
            cor = COR_SITUACAO.get(item.situacao, "#1f1f1f")
            rotulo = ROTULO_SITUACAO.get(item.situacao, item.situacao.value)
            limite = f"{item.limite:%d/%m}" if item.limite else "—"
            linhas.append(
                '<tr><td style="padding:8px 6px;border-bottom:1px solid #eee;'
                'font-size:14px;white-space:nowrap;">'
                f"{item.inicio:%d/%m %H:%M}</td>"
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:14px;">{escape(item.paciente.nome)}</td>'
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:13px;color:{CINZA};white-space:nowrap;">{limite}</td>'
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:13px;color:{cor};white-space:nowrap;">{escape(rotulo)}</td></tr>'
            )
        cabecalho = "".join(
            f'<th align="left" style="padding:6px;font-size:11px;color:{CINZA};'
            f'text-transform:uppercase;">{escape(c)}</th>'
            for c in ("Retorno", "Paciente", "Limite", "Situação")
        )
        return (
            self._titulo_secao(
                f"Agenda de retornos (limite de {INTERVALO_MAXIMO_DIAS} dias)"
            )
            + '<table role="presentation" style="border-collapse:collapse;width:100%;">'
            + f"<tr>{cabecalho}</tr>"
            + "".join(linhas)
            + "</table>"
        )

    def _bloco_quadro_consultas(self) -> str:
        if not self.cruzamento:
            return ""
        linhas = []
        for paciente in sorted(self.ativos, key=lambda p: p.nome):
            resumo = self.cruzamento.de(paciente)
            if resumo is None:
                continue
            if resumo.sem_dados:
                estado, cor = "sem registro", CINZA
            elif resumo.deficit > 0:
                estado, cor = f"faltam {resumo.deficit}", VERMELHO
            elif resumo.esgotadas:
                estado, cor = "esgotadas", AMBAR
            else:
                estado, cor = "em dia", VERDE
            barra = self._barra(resumo.realizadas, resumo.previstas_total)
            linhas.append(
                '<tr><td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:14px;">{escape(paciente.nome)}</td>'
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:13px;color:{CINZA};">'
                f"{escape(profissional_de(paciente))}</td>"
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:13px;color:{CINZA};">{escape(paciente.plano.nome)}</td>'
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:14px;white-space:nowrap;">{resumo.realizadas} de '
                f"{resumo.previstas_total}{barra}</td>"
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:13px;color:{CINZA};white-space:nowrap;">'
                f"{resumo.previstas_ate_hoje}</td>"
                '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                f'font-size:13px;color:{cor};white-space:nowrap;">{escape(estado)}</td></tr>'
            )
        if not linhas:
            return ""
        cabecalhos = (
            "Paciente",
            "Profissional",
            "Plano",
            "Feitas",
            "Previstas até hoje",
            "Situação",
        )
        cabecalho = "".join(
            f'<th align="left" style="padding:6px;font-size:11px;color:{CINZA};'
            f'text-transform:uppercase;">{escape(c)}</th>'
            for c in cabecalhos
        )
        return (
            self._titulo_secao("Consultas por paciente")
            + '<table role="presentation" style="border-collapse:collapse;width:100%;">'
            + f"<tr>{cabecalho}</tr>"
            + "".join(linhas)
            + "</table>"
        )

    @staticmethod
    def _barra(feitas: int, total: int) -> str:
        """Barrinha de progresso em texto, que sobrevive a qualquer cliente."""
        if total <= 0 or total > 12:
            return ""
        cheias = min(feitas, total)
        return (
            f'<span style="color:{VERDE};letter-spacing:1px;"> '
            + "•" * cheias
            + f'</span><span style="color:#d0d0d0;letter-spacing:1px;">'
            + "•" * (total - cheias)
            + "</span>"
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
            cor = VERMELHO if urgente else AMBAR
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

    def _bloco_sem_data(self) -> str:
        faltantes = self.sem_data_de_consulta
        if not faltantes:
            return ""
        return (
            '<div style="background:#eef4ff;border:1px solid #c7d8f5;border-radius:8px;'
            'padding:12px 14px;margin:20px 0;font-size:13px;">'
            f'<b>{len(faltantes)} paciente(s) sem data da última consulta.</b><br>'
            f"Para esses, o limite de {INTERVALO_MAXIMO_DIAS} dias não pode ser "
            "aferido — eles ficam fora do alarme para não gerar atraso falso. "
            "A data vem da última avaliação antropométrica do WebDiet; com essa "
            "exportação, o alarme passa a cobrir todo mundo.</div>"
        )

    def _bloco_conferir(self) -> str:
        itens = self._conferir()
        if not itens:
            return ""
        lista = "".join(
            f'<li style="margin-bottom:6px;">{escape(i)}</li>' for i in itens
        )
        return (
            self._titulo_secao("Conferir manualmente")
            + f'<p style="font-size:13px;color:{CINZA};margin:0 0 8px;">'
            "O agente não associou estes nomes sozinho para não arriscar contar "
            "consulta na pessoa errada.</p>"
            f'<ul style="margin:0;padding-left:18px;font-size:14px;">{lista}</ul>'
        )

    def _bloco_vigencias(self) -> str:
        proximos = [p for p in self.ativos if 0 <= p.dias_para_vencer_em(self.hoje) <= 15]
        if not proximos:
            return ""
        itens = "".join(
            f'<li style="margin-bottom:6px;"><strong>{escape(p.nome)}</strong> '
            f'<span style="color:{CINZA};">({escape(p.plano.nome)})</span> — '
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
            f'font-size:12px;color:{CINZA};">'
            "Enviado pelo agente de agendamento, da sua máquina. "
            "Nenhuma mensagem foi enviada aos pacientes.</p>"
        )


def montar(
    pacientes: list[Paciente],
    agendamentos: list[Agendamento],
    alertas: list[Alerta],
    hoje: date | None = None,
    cruzamento: Cruzamento | None = None,
    titulo_filtro: str = "",
) -> Relatorio:
    return Relatorio(pacientes, agendamentos, alertas, hoje, cruzamento, titulo_filtro)
