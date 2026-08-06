"""Instruções de contato para um agente de IA que marca as consultas.

Gera duas saídas do mesmo conteúdo: um JSON, que é o formato correto para
outro programa consumir, e uma página para virar PDF, para leitura humana
ou para agentes que só aceitam documento.

O texto é escrito para ser lido por máquina: campos rotulados, um registro
por bloco, sem tabela — tabela de PDF embaralha ao ser extraída, e uma
coluna trocada aqui vira mensagem para o paciente errado.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from html import escape
from pathlib import Path

from .modelos import Agendamento, SituacaoAgendamento
from .regras import INTERVALO_MAXIMO_DIAS

# Atraso acima disto não é esquecimento de agenda: é cadastro suspeito.
ATRASO_IMPLAUSIVEL_DIAS = 365


@dataclass
class ContatoParaMarcar:
    prioridade: int
    nome: str
    whatsapp: str | None
    plano: str
    ultima_consulta: str | None
    dias_desde_ultima_consulta: int | None
    limite_30_dias: str
    dias_de_atraso: int
    agendar_ate: str
    horario_sugerido: str | None
    acao: str
    observacao: str = ""
    conferir_antes: bool = False


def _texto(valor: date | None) -> str | None:
    return f"{valor:%d/%m/%Y}" if valor else None


def montar_contatos(
    agendamentos: list[Agendamento], hoje: date | None = None
) -> tuple[list[ContatoParaMarcar], list[ContatoParaMarcar]]:
    """Separa quem o agente pode contatar de quem precisa de conferência.

    Devolve ``(contatar, conferir_antes)``. Cadastro inconsistente não vai
    para a fila de contato: mandar mensagem baseada em dado errado custa
    mais caro que atrasar um dia.
    """
    hoje = hoje or date.today()
    contatar: list[ContatoParaMarcar] = []
    reter: list[ContatoParaMarcar] = []

    candidatos = [
        a
        for a in agendamentos
        if a.situacao
        in (
            SituacaoAgendamento.ATRASADO,
            SituacaoAgendamento.AGENDAVEL,
            SituacaoAgendamento.SEM_VAGA,
        )
    ]

    def urgencia(a: Agendamento):
        atraso = (hoje - a.limite).days if a.limite else 0
        return (-atraso, a.limite or date.max, a.paciente.nome)

    for posicao, agendamento in enumerate(sorted(candidatos, key=urgencia), start=1):
        paciente = agendamento.paciente
        limite = agendamento.limite or paciente.plano_fim
        atraso = max(0, (hoje - limite).days)
        desde = (
            (hoje - paciente.ultima_consulta).days if paciente.ultima_consulta else None
        )
        teto = min(limite, paciente.plano_fim) if limite >= hoje else paciente.plano_fim

        conferir = False
        observacao = ""
        if paciente.ultima_consulta is None:
            conferir = True
            observacao = (
                "Sem registro de consulta no WebDiet. Não dá para afirmar atraso; "
                "confirme a última consulta antes de falar em prazo."
            )
        elif desde is not None and desde > ATRASO_IMPLAUSIVEL_DIAS:
            conferir = True
            observacao = (
                f"Última consulta há {desde} dias, mas o plano está ativo. "
                "Cadastro provavelmente desatualizado — confirme antes de contatar."
            )
        elif agendamento.situacao is SituacaoAgendamento.SEM_VAGA:
            observacao = (
                "Não há horário livre dentro do prazo. Ofereça a primeira vaga "
                "disponível e registre que o limite foi ultrapassado."
            )

        item = ContatoParaMarcar(
            prioridade=posicao,
            nome=paciente.nome,
            whatsapp=paciente.whatsapp,
            plano=paciente.plano.nome,
            ultima_consulta=_texto(paciente.ultima_consulta),
            dias_desde_ultima_consulta=desde,
            limite_30_dias=f"{limite:%d/%m/%Y}",
            dias_de_atraso=atraso,
            agendar_ate=f"{teto:%d/%m/%Y}",
            horario_sugerido=(
                f"{agendamento.inicio:%d/%m/%Y %H:%M}" if agendamento.inicio else None
            ),
            acao="confirmar_cadastro" if conferir else "marcar_consulta",
            observacao=observacao,
            conferir_antes=conferir,
        )
        (reter if conferir else contatar).append(item)

    for posicao, item in enumerate(contatar, start=1):
        item.prioridade = posicao
    for posicao, item in enumerate(reter, start=1):
        item.prioridade = posicao
    return contatar, reter


REGRAS = [
    f"O retorno NUNCA pode ser marcado mais de {INTERVALO_MAXIMO_DIAS} dias depois "
    "da última consulta. Este é um teto rígido, não uma meta.",
    "O retorno NUNCA pode ser marcado depois da data em 'agendar_ate'. Essa data "
    "já considera o limite de 30 dias e o fim da vigência do plano — vale a que "
    "vier primeiro.",
    "Contate na ordem do campo 'prioridade': 1 primeiro. A ordem é por dias de "
    "atraso, do maior para o menor.",
    "Ofereça o 'horario_sugerido' como primeira opção. Se o paciente recusar, "
    "ofereça outro horário anterior a 'agendar_ate'.",
    "Confirme a identidade do paciente antes de tratar de qualquer assunto de "
    "saúde ou de plano.",
    "Ao fechar o horário, registre a data marcada e encerre o contato.",
]

PROIBIDO = [
    "Não contate ninguém da lista CONFERIR ANTES DE CONTATAR sem antes checar o "
    "cadastro com o profissional.",
    "Não marque nada depois da data em 'agendar_ate', mesmo que o paciente peça.",
    "Não informe resultado de exame, evolução de peso, conduta clínica ou "
    "qualquer dado de saúde. O contato é só para marcar horário.",
    "Não afirme quantas consultas o paciente já fez: este relatório não tem "
    "essa informação de forma confiável.",
    "Não insista após duas tentativas sem resposta. Devolva o caso ao "
    "profissional.",
    "Não invente horário que não esteja na agenda.",
]


def montar_json(
    contatar: list[ContatoParaMarcar],
    conferir: list[ContatoParaMarcar],
    hoje: date | None = None,
) -> dict:
    hoje = hoje or date.today()
    return {
        "gerado_em": hoje.isoformat(),
        "objetivo": "Entrar em contato por WhatsApp para marcar consulta de retorno.",
        "limite_dias_entre_consultas": INTERVALO_MAXIMO_DIAS,
        "regras": REGRAS,
        "proibido": PROIBIDO,
        "campos": {
            "prioridade": "Ordem de contato. 1 é o mais urgente.",
            "agendar_ate": "Data máxima para o retorno. Teto rígido.",
            "limite_30_dias": "Quando o prazo de 30 dias vence ou venceu.",
            "dias_de_atraso": "Quantos dias já passaram do limite. 0 = dentro do prazo.",
            "horario_sugerido": "Vaga livre na agenda, para oferecer primeiro.",
            "acao": "marcar_consulta ou confirmar_cadastro.",
        },
        "contatar": [asdict(c) for c in contatar],
        "conferir_antes_de_contatar": [asdict(c) for c in conferir],
        "totais": {"contatar": len(contatar), "conferir": len(conferir)},
    }


def gravar_json(dados: dict, destino: str | Path) -> Path:
    caminho = Path(destino).expanduser()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return caminho


def _bloco(item: ContatoParaMarcar) -> str:
    """Um registro por bloco, com campo rotulado em cada linha.

    Formato escolhido para sobreviver à extração de texto do PDF: sem
    tabela, sem coluna, uma informação por linha.
    """
    linhas = [
        ("PRIORIDADE", str(item.prioridade)),
        ("PACIENTE", item.nome),
        ("WHATSAPP", item.whatsapp or "não cadastrado"),
        ("PLANO", item.plano),
        ("ULTIMA_CONSULTA", item.ultima_consulta or "sem registro"),
        ("LIMITE_30_DIAS", item.limite_30_dias),
        ("DIAS_DE_ATRASO", str(item.dias_de_atraso)),
        ("AGENDAR_ATE", item.agendar_ate),
        ("HORARIO_SUGERIDO", item.horario_sugerido or "nenhum dentro do prazo"),
        ("ACAO", item.acao),
    ]
    if item.observacao:
        linhas.append(("OBSERVACAO", item.observacao))
    corpo = "".join(
        f'<div style="font-size:12px;line-height:1.45;">'
        f'<b>{escape(rotulo)}:</b> {escape(valor)}</div>'
        for rotulo, valor in linhas
    )
    borda = "#b3261e" if item.conferir_antes else "#1a7f4b"
    return (
        f'<div style="border-left:3px solid {borda};padding:8px 10px;margin:0 0 10px;'
        f'background:#fafafa;page-break-inside:avoid;">{corpo}</div>'
    )


def montar_html(
    contatar: list[ContatoParaMarcar],
    conferir: list[ContatoParaMarcar],
    hoje: date | None = None,
) -> str:
    hoje = hoje or date.today()

    def lista(titulo: str, itens: list[str], cor: str) -> str:
        pontos = "".join(
            f'<li style="margin-bottom:5px;">{escape(i)}</li>' for i in itens
        )
        return (
            f'<h2 style="font-size:15px;margin:20px 0 6px;color:{cor};">{titulo}</h2>'
            f'<ol style="margin:0;padding-left:20px;font-size:12.5px;'
            f'line-height:1.5;">{pontos}</ol>'
        )

    blocos = [
        '<div style="font-family:Arial,Helvetica,sans-serif;max-width:760px;'
        'color:#1f1f1f;line-height:1.5;">',
        '<h1 style="font-size:19px;margin:0 0 2px;">Instruções de contato para '
        "agendamento</h1>",
        f'<p style="margin:0 0 4px;color:#5f6368;font-size:13px;">'
        f"Documento gerado em {hoje:%d/%m/%Y} · destinado a um agente de IA</p>",
        '<p style="font-size:12.5px;background:#eef4ff;border:1px solid #c7d8f5;'
        'border-radius:6px;padding:10px;margin:0 0 4px;">'
        "<b>OBJETIVO:</b> entrar em contato por WhatsApp com os pacientes listados "
        "e marcar a consulta de retorno, respeitando as regras abaixo.</p>",
        lista("REGRAS", REGRAS, "#1a7f4b"),
        lista("PROIBIDO", PROIBIDO, "#b3261e"),
    ]

    blocos.append(
        f'<h2 style="font-size:15px;margin:22px 0 6px;">CONTATAR '
        f'<span style="font-weight:400;color:#5f6368;">'
        f"({len(contatar)} pacientes)</span></h2>"
    )
    if contatar:
        blocos.append(
            '<p style="font-size:12px;color:#5f6368;margin:0 0 10px;">'
            "Um bloco por paciente, na ordem de contato.</p>"
        )
        blocos.extend(_bloco(item) for item in contatar)
    else:
        blocos.append('<p style="font-size:13px;">Ninguém para contatar hoje.</p>')

    blocos.append(
        f'<h2 style="font-size:15px;margin:22px 0 6px;color:#b3261e;">'
        f"CONFERIR ANTES DE CONTATAR "
        f'<span style="font-weight:400;color:#5f6368;">'
        f"({len(conferir)} pacientes)</span></h2>"
    )
    blocos.append(
        '<p style="font-size:12.5px;margin:0 0 10px;">'
        "<b>NÃO envie mensagem para estes pacientes.</b> O cadastro está "
        "incompleto ou inconsistente. Devolva a lista ao profissional para "
        "conferência.</p>"
    )
    blocos.extend(_bloco(item) for item in conferir)

    blocos.append(
        '<p style="font-size:11.5px;color:#5f6368;margin-top:24px;padding-top:10px;'
        'border-top:1px solid #e0e0e0;">'
        "Este documento não contém informação clínica. Os dados vêm do LiveClin "
        "(plano e vigência) e do WebDiet (data da última alteração da dieta). "
        "Existe uma versão em JSON com o mesmo conteúdo, mais confiável para "
        "leitura automática.</p></div>"
    )
    return "".join(blocos)
