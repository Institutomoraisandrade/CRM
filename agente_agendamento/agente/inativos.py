"""Pacientes que pararam, e há quanto tempo.

Inativo aqui é quem tem o plano vencido ou o cadastro marcado como
inativo no LiveClin. O tempo é contado da data mais recente que se sabe
dele: a última consulta do WebDiet, ou o fim do plano quando não há
avaliação registrada.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from html import escape

from .consultas import Cruzamento
from .filtros import profissional_de
from .modelos import Paciente, StatusPaciente

# Faixas de tempo parado, para agrupar o esforço de reativação.
FAIXAS: tuple[tuple[int, str], ...] = (
    (30, "até 1 mês"),
    (90, "1 a 3 meses"),
    (180, "3 a 6 meses"),
    (365, "6 meses a 1 ano"),
)
FAIXA_LONGA = "mais de 1 ano"


@dataclass
class PacienteInativo:
    paciente: Paciente
    desde: date
    origem_da_data: str
    consultas_feitas: int = 0
    consultas_previstas: int = 0

    @property
    def nome(self) -> str:
        return self.paciente.nome

    def dias_parado(self, hoje: date) -> int:
        return max(0, (hoje - self.desde).days)

    def tempo_parado(self, hoje: date) -> str:
        dias = self.dias_parado(hoje)
        if dias < 30:
            return f"{dias} dia" + ("s" if dias != 1 else "")
        meses = dias // 30
        if meses < 12:
            return f"{meses} " + ("mês" if meses == 1 else "meses")
        anos = dias // 365
        resto = (dias % 365) // 30
        texto = f"{anos} ano" + ("s" if anos > 1 else "")
        if resto:
            texto += f" e {resto} " + ("mês" if resto == 1 else "meses")
        return texto

    def faixa(self, hoje: date) -> str:
        dias = self.dias_parado(hoje)
        for limite, rotulo in FAIXAS:
            if dias <= limite:
                return rotulo
        return FAIXA_LONGA

    @property
    def concluiu_o_plano(self) -> bool:
        """Terminou as consultas contratadas antes de parar."""
        return (
            self.consultas_previstas > 0
            and self.consultas_feitas >= self.consultas_previstas
        )


def levantar(
    pacientes: list[Paciente],
    hoje: date | None = None,
    cruzamento: Cruzamento | None = None,
) -> list[PacienteInativo]:
    """Lista quem está parado, do que parou mais recentemente ao mais antigo.

    A ordem é proposital: quem saiu há pouco costuma ser mais fácil de
    trazer de volta do que quem sumiu há um ano.
    """
    hoje = hoje or date.today()
    inativos: list[PacienteInativo] = []

    for paciente in pacientes:
        vencido = paciente.plano_fim < hoje
        if paciente.status is StatusPaciente.ATIVO and not vencido:
            continue
        if paciente.status is StatusPaciente.PAUSADO:
            # Pausado é uma interrupção combinada, não um abandono.
            continue

        resumo = cruzamento.de(paciente) if cruzamento else None
        ultima = paciente.ultima_consulta
        if resumo is not None and resumo.ultima is not None:
            ultima = resumo.ultima

        if ultima is not None and ultima >= paciente.plano_inicio:
            desde, origem = ultima, "última consulta"
        else:
            desde, origem = paciente.plano_fim, "fim do plano"

        inativos.append(
            PacienteInativo(
                paciente=paciente,
                desde=min(desde, hoje),
                origem_da_data=origem,
                consultas_feitas=resumo.realizadas if resumo else 0,
                consultas_previstas=resumo.previstas_total if resumo else 0,
            )
        )

    inativos.sort(key=lambda i: (-i.desde.toordinal(), i.nome))
    return inativos


def agrupar_por_faixa(
    inativos: list[PacienteInativo], hoje: date
) -> dict[str, list[PacienteInativo]]:
    ordem = [rotulo for _, rotulo in FAIXAS] + [FAIXA_LONGA]
    grupos: dict[str, list[PacienteInativo]] = {}
    for item in inativos:
        grupos.setdefault(item.faixa(hoje), []).append(item)
    return {rotulo: grupos[rotulo] for rotulo in ordem if rotulo in grupos}


class RelatorioInativos:
    """Monta o e-mail da lista de inativos."""

    CINZA = "#5f6368"

    def __init__(
        self, inativos: list[PacienteInativo], hoje: date | None = None
    ) -> None:
        self.hoje = hoje or date.today()
        self.inativos = inativos

    @property
    def assunto(self) -> str:
        if not self.inativos:
            return f"Pacientes inativos — nenhum em {self.hoje:%d/%m/%Y}"
        plural = "paciente" if len(self.inativos) == 1 else "pacientes"
        return f"{len(self.inativos)} {plural} inativos — {self.hoje:%d/%m/%Y}"

    def texto(self) -> str:
        linhas = [
            f"Pacientes inativos — {self.hoje:%d/%m/%Y}",
            "",
            f"Total: {len(self.inativos)}",
        ]
        if not self.inativos:
            linhas.append("Nenhum paciente inativo.")
            return "\n".join(linhas)

        for faixa, itens in agrupar_por_faixa(self.inativos, self.hoje).items():
            linhas += ["", f"{faixa.upper()} ({len(itens)})", "-" * 52]
            for item in itens:
                consultas = ""
                if item.consultas_previstas:
                    consultas = (
                        f" · {item.consultas_feitas} de "
                        f"{item.consultas_previstas} consultas"
                    )
                linhas.append(
                    f"  {item.nome} ({profissional_de(item.paciente)} · "
                    f"{item.paciente.plano.nome}){consultas}"
                )
                linhas.append(
                    f"      parado há {item.tempo_parado(self.hoje)} — "
                    f"{item.origem_da_data} em {item.desde:%d/%m/%Y}"
                )
                if item.paciente.whatsapp:
                    linhas.append(f"      WhatsApp: {item.paciente.whatsapp}")

        linhas += ["", "-" * 52, "Enviado pelo agente. Nada foi enviado aos pacientes."]
        return "\n".join(linhas)

    def html(self) -> str:
        if not self.inativos:
            corpo = (
                '<p style="font-size:14px;">Nenhum paciente inativo hoje.</p>'
            )
        else:
            corpo = self._resumo() + self._grupos()
        return (
            '<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,'
            'sans-serif;max-width:680px;margin:0 auto;padding:16px;color:#1f1f1f;'
            'line-height:1.5;">'
            '<h1 style="font-size:20px;margin:0 0 4px;">Pacientes inativos</h1>'
            f'<p style="margin:0 0 20px;color:{self.CINZA};font-size:14px;">'
            f"{self.hoje:%d/%m/%Y}</p>" + corpo + self._rodape() + "</div>"
        )

    def _resumo(self) -> str:
        grupos = agrupar_por_faixa(self.inativos, self.hoje)
        celulas = "".join(
            '<td style="padding:10px 12px;border:1px solid #e0e0e0;border-radius:6px;'
            'text-align:center;">'
            f'<div style="font-size:22px;font-weight:600;">{len(itens)}</div>'
            f'<div style="font-size:12px;color:{self.CINZA};">{escape(faixa)}</div>'
            "</td>"
            for faixa, itens in grupos.items()
        )
        return (
            f'<p style="font-size:14px;margin:0 0 12px;"><strong>'
            f"{len(self.inativos)}</strong> pacientes parados, do mais recente ao "
            "mais antigo — os de cima costumam ser os mais fáceis de trazer de "
            "volta.</p>"
            '<table role="presentation" style="border-collapse:separate;'
            f'border-spacing:6px;width:100%;margin-bottom:20px;"><tr>{celulas}</tr>'
            "</table>"
        )

    def _grupos(self) -> str:
        blocos = []
        for faixa, itens in agrupar_por_faixa(self.inativos, self.hoje).items():
            linhas = []
            for item in itens:
                consultas = ""
                if item.consultas_previstas:
                    marca = " ✓" if item.concluiu_o_plano else ""
                    consultas = (
                        f'<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                        f'font-size:13px;color:{self.CINZA};white-space:nowrap;">'
                        f"{item.consultas_feitas} de {item.consultas_previstas}"
                        f"{marca}</td>"
                    )
                else:
                    consultas = (
                        '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                        f'font-size:13px;color:{self.CINZA};">—</td>'
                    )
                linhas.append(
                    '<tr><td style="padding:8px 6px;border-bottom:1px solid #eee;'
                    f'font-size:14px;">{escape(item.nome)}'
                    f'<div style="font-size:12px;color:{self.CINZA};">'
                    f"{escape(profissional_de(item.paciente))} · "
                    f"{escape(item.paciente.plano.nome)}</div></td>"
                    '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                    'font-size:14px;font-weight:600;white-space:nowrap;">'
                    f"{escape(item.tempo_parado(self.hoje))}"
                    f'<div style="font-size:11px;font-weight:400;color:{self.CINZA};">'
                    f"{escape(item.origem_da_data)} {item.desde:%d/%m/%Y}</div></td>"
                    f"{consultas}"
                    '<td style="padding:8px 6px;border-bottom:1px solid #eee;'
                    f'font-size:13px;color:{self.CINZA};white-space:nowrap;">'
                    f"{escape(item.paciente.whatsapp or '—')}</td></tr>"
                )
            cabecalho = "".join(
                f'<th align="left" style="padding:6px;font-size:11px;'
                f'color:{self.CINZA};text-transform:uppercase;">{escape(c)}</th>'
                for c in ("Paciente", "Parado há", "Consultas", "WhatsApp")
            )
            blocos.append(
                '<h2 style="font-size:15px;margin:24px 0 8px;padding-bottom:6px;'
                f'border-bottom:1px solid #e0e0e0;">{escape(faixa)} '
                f'<span style="color:{self.CINZA};font-weight:400;">'
                f"({len(itens)})</span></h2>"
                '<table role="presentation" style="border-collapse:collapse;'
                f'width:100%;"><tr>{cabecalho}</tr>' + "".join(linhas) + "</table>"
            )
        return "".join(blocos)

    def _rodape(self) -> str:
        return (
            '<p style="margin-top:28px;padding-top:12px;border-top:1px solid #e0e0e0;'
            f'font-size:12px;color:{self.CINZA};">'
            "O ✓ marca quem concluiu as consultas do plano antes de parar. "
            "Nenhuma mensagem foi enviada aos pacientes.</p>"
        )
