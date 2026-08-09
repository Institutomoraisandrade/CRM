"""Quem ainda não tem consulta marcada na agenda.

Cruza a lista de pacientes com os eventos do Google Calendar e separa
quem já está agendado de quem ainda precisa ser chamado.

Duas decisões definem a precisão deste módulo:

**Um lembrete não é um agendamento.** A agenda usa ``🔷 AGENDAR — Fulano``
para marcar que alguém *precisa* ser agendado. Tratar isso como consulta
marcada esconderia justamente quem está esperando.

**Só consulta futura conta.** Consulta que já aconteceu não impede a
próxima — quem foi atendido semana passada volta para a fila.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .nomes import casar, tokens

# Compromissos que não são paciente.
NAO_E_PACIENTE = re.compile(
    r"igreja|a ponte|junta comercial|reuni[ãa]o cont|m[óo]veis|instala[çc]",
    re.IGNORECASE,
)

# Marcadores de pendência: o evento é um lembrete, não uma consulta.
PENDENTE = re.compile(r"agendar|standby|fechar venda", re.IGNORECASE)

# Prefixos que enfeitam o título e não fazem parte do nome.
_RUIDO = re.compile(
    r"(?i)^(consulta agendada|consulta confirmada|consulta|nutricionista consulta"
    r"|on-?line|agendar)\b"
)
_SUFIXO = re.compile(r"(?i)\b(retorno|primeira consulta|confirmado|agendar)\b")
_ROTULO = re.compile(r"(?i)^[^\w(]*(fechar venda|standby)\s*[-—|]*\s*")

# Anotações de sessão que a agenda cola no nome: "Fulana on-line 2/3",
# "Beltrano renov", "Sicrana parceira". Não fazem parte do nome e, se
# ficarem, atrapalham o casamento.
_SESSAO = re.compile(
    r"(?i)\b(\d+\s*/\s*\d+|on-?line|presencial|renov\w*|parc\w*)\b"
)


def nome_do_evento(titulo: str) -> str:
    """Extrai o nome do paciente do título do evento.

    A agenda é escrita à mão e cada semana inventa um formato novo:
    ``Consulta agendada ( Ramon Casado )``, ``🟢 CONSULTA — Helga Barros
    — CONFIRMADO``, ``Nutricionista Consulta - Renan Costa Rego`` ou só
    ``Thiago Porto``. Todos devem chegar ao mesmo nome.
    """
    texto = _ROTULO.sub("", titulo).strip()
    texto = re.sub(r"^[^\w(]+", "", texto).strip()

    entre_parenteses = re.search(r"\(([^)]+)\)", texto)
    if entre_parenteses:
        texto = entre_parenteses.group(1).strip()
    else:
        texto = _RUIDO.sub("", texto).strip()
        texto = re.sub(r"^[\s\-—|]+", "", texto)
        for separador in ("—", "|", " - "):
            if separador in texto:
                texto = texto.split(separador)[0]

    texto = _SUFIXO.sub("", texto)
    texto = _SESSAO.sub("", texto)
    texto = re.sub(r"(?i)\s*\+.*$", "", texto)  # "Fulano + Beltrana"
    texto = re.sub(r"[\s\-—|]+$", "", texto).strip()
    return " ".join(texto.split())


@dataclass
class Agenda:
    """Os nomes que aparecem na agenda, já classificados."""

    marcados: dict[str, str] = field(default_factory=dict)  # nome -> data ISO
    lembretes: set[str] = field(default_factory=set)


def ler_agenda(eventos: list[dict], hoje: date) -> Agenda:
    """Classifica os eventos do Google Calendar.

    ``marcados`` só recebe consulta de verdade com data a partir de hoje;
    lembrete de "AGENDAR" e standby vão para ``lembretes``, que sinaliza
    sem impedir o contato.
    """
    agenda = Agenda()
    for evento in eventos:
        titulo = (evento.get("summary") or "").strip()
        if not titulo or NAO_E_PACIENTE.search(titulo):
            continue

        inicio = evento.get("start", {})
        quando = inicio.get("dateTime") or inicio.get("date") or ""
        if not quando:
            continue

        nome = nome_do_evento(titulo)
        if not nome:
            continue

        if PENDENTE.search(titulo):
            agenda.lembretes.add(nome)
            continue

        dia = date.fromisoformat(quando[:10])
        if dia < hoje:
            continue
        # Vale a consulta mais próxima.
        if nome not in agenda.marcados or quando[:10] < agenda.marcados[nome]:
            agenda.marcados[nome] = quando[:10]
    return agenda


def _contido(a: str, b: str) -> bool:
    """Um nome cabe dentro do outro.

    O cadastro traz "Roberto Santos Miranda"; a agenda, "Roberto Santos".
    São a mesma pessoa, e o casamento por semelhança não alcança isso
    porque a diferença de tamanho derruba a nota. Exigimos dois tokens em
    comum — "Ana Souza" e "Ana Souza Lima" passam, "Ana" e "Ana Souza"
    não, porque um primeiro nome sozinho não identifica ninguém.
    """
    ta, tb = set(tokens(a)), set(tokens(b))
    curto, longo = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return len(curto) >= 2 and curto <= longo


def corresponder(nome: str, candidatos) -> str | None:
    """Acha ``nome`` entre ``candidatos``, por semelhança ou por conter."""
    lista = sorted(candidatos)
    achado = casar(nome, lista)
    if achado.encontrou:
        return achado.escolhido
    for candidato in lista:
        if _contido(nome, candidato):
            return candidato
    return None


def homonimos(nome: str, candidatos) -> list[str]:
    """Candidatos que dividem o primeiro nome sem dar para decidir.

    "Gabriel" no cadastro contra "Gabriel Bezerra" e "Gabriel Pimentel"
    na agenda: são três pessoas possíveis e nenhuma evidência para
    escolher. Devolvemos os candidatos para conferência humana em vez de
    chutar.
    """
    proprios = tokens(nome)
    if not proprios:
        return []
    primeiro = proprios[0]
    achados = [c for c in sorted(candidatos) if tokens(c) and tokens(c)[0] == primeiro]
    # Só é dúvida quando um dos lados é um nome solto.
    if len(proprios) > 1 and all(len(tokens(c)) > 1 for c in achados):
        return []
    return achados


@dataclass
class Pendencia:
    """Um paciente e o que a agenda diz sobre ele."""

    nome: str
    plano: str
    fim_do_plano: str
    dias_restantes: int
    whatsapp: str = ""
    tem_lembrete: bool = False
    observacao: str = ""


@dataclass
class Separacao:
    a_agendar: list[Pendencia] = field(default_factory=list)
    conferir: list[Pendencia] = field(default_factory=list)
    ja_agendados: list[tuple[str, str]] = field(default_factory=list)
    de_outro_profissional: list[tuple[str, str]] = field(default_factory=list)


def separar(
    pacientes: list[Pendencia],
    agenda: Agenda,
    agenda_de_outro: set[str] | None = None,
) -> Separacao:
    """Divide os pacientes entre agendados, a agendar e duvidosos.

    ``agenda_de_outro`` são os nomes que aparecem na agenda de outro
    profissional. Serve enquanto a exportação não traz a etiqueta do
    responsável: quem aparece lá é dele, não desta fila.
    """
    outro = agenda_de_outro or set()
    resultado = Separacao()

    for paciente in pacientes:
        marcado = corresponder(paciente.nome, agenda.marcados)
        if marcado:
            resultado.ja_agendados.append((paciente.nome, agenda.marcados[marcado]))
            continue

        duvida = homonimos(paciente.nome, agenda.marcados)
        if duvida:
            paciente.observacao = (
                f"a agenda tem {duvida[0]!r} em {agenda.marcados[duvida[0]]} — "
                "confirme se é o mesmo paciente antes de chamar"
            )
            resultado.conferir.append(paciente)
            continue

        de_outro = corresponder(paciente.nome, outro)
        if de_outro:
            resultado.de_outro_profissional.append((paciente.nome, de_outro))
            continue

        duvida = homonimos(paciente.nome, outro)
        if duvida:
            paciente.observacao = (
                f"a agenda do outro profissional tem {duvida[0]!r} — "
                "confirme de quem é o paciente"
            )
            resultado.conferir.append(paciente)
            continue

        paciente.tem_lembrete = corresponder(paciente.nome, agenda.lembretes) is not None
        resultado.a_agendar.append(paciente)

    resultado.a_agendar.sort(key=lambda p: p.dias_restantes)
    resultado.conferir.sort(key=lambda p: p.dias_restantes)
    resultado.ja_agendados.sort(key=lambda par: par[1])
    resultado.de_outro_profissional.sort()
    return resultado


def _escapar(texto: str) -> str:
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _urgencia(dias: int) -> tuple[str, str]:
    """Cor e rótulo pela folga que resta no plano."""
    if dias <= 15:
        return "#b3261e", "vence em breve"
    if dias <= 45:
        return "#a06400", "atenção"
    return "#3c6e47", "com folga"


def _linha(paciente: Pendencia) -> str:
    cor, rotulo = _urgencia(paciente.dias_restantes)
    marcas = []
    if paciente.tem_lembrete:
        marcas.append("já existe lembrete <b>AGENDAR</b> na agenda")
    if paciente.observacao:
        marcas.append(_escapar(paciente.observacao))
    nota = (
        f'<div class="nota">{" · ".join(marcas)}</div>' if marcas else ""
    )
    return f"""
    <tr>
      <td class="nome">{_escapar(paciente.nome)}{nota}</td>
      <td>{_escapar(paciente.whatsapp)}</td>
      <td>{_escapar(paciente.plano)}</td>
      <td>{_escapar(paciente.fim_do_plano)}</td>
      <td style="color:{cor};white-space:nowrap">
        <b>{paciente.dias_restantes}d</b><br><span class="rotulo">{rotulo}</span>
      </td>
    </tr>"""


def _tabela(pacientes: list[Pendencia]) -> str:
    if not pacientes:
        return '<p class="vazio">Ninguém nesta lista.</p>'
    return f"""
    <table>
      <thead>
        <tr><th>Paciente</th><th>WhatsApp</th><th>Plano</th>
            <th>Plano vence</th><th>Restam</th></tr>
      </thead>
      <tbody>{"".join(_linha(p) for p in pacientes)}</tbody>
    </table>"""


ESTILO = """
body { font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
       color: #1b1b1b; font-size: 13px; line-height: 1.45; }
h1 { font-size: 20px; margin: 0 0 4px; }
h2 { font-size: 15px; margin: 26px 0 6px; padding-bottom: 4px;
     border-bottom: 2px solid #1b1b1b; }
.sub { color: #555; margin: 0 0 18px; }
table { border-collapse: collapse; width: 100%; }
th { text-align: left; font-size: 11px; text-transform: uppercase;
     letter-spacing: .04em; color: #555; padding: 6px 8px;
     border-bottom: 1px solid #ccc; }
td { padding: 7px 8px; border-bottom: 1px solid #eee; vertical-align: top; }
.nome { font-weight: 600; }
.nota { font-weight: 400; font-size: 11px; color: #7a4a00; margin-top: 2px; }
.rotulo { font-size: 10px; text-transform: uppercase; letter-spacing: .03em; }
.vazio { color: #777; font-style: italic; }
.aviso { background: #fff6e5; border-left: 3px solid #a06400;
         padding: 10px 12px; margin: 14px 0; font-size: 12px; }
.leve { color: #555; font-size: 12px; }
tr { page-break-inside: avoid; }
"""


def montar_html(separacao: Separacao, hoje: date, aviso: str = "") -> str:
    """Monta o documento para leitura humana."""
    dia = hoje.strftime("%d/%m/%Y")
    bloco_aviso = f'<div class="aviso">{aviso}</div>' if aviso else ""

    agendados = "".join(
        f"<li>{_escapar(n)} — <b>{date.fromisoformat(d).strftime('%d/%m')}</b></li>"
        for n, d in separacao.ja_agendados
    )
    outros = "".join(
        f"<li>{_escapar(n)} <span class='leve'>(agenda: {_escapar(e)})</span></li>"
        for n, e in separacao.de_outro_profissional
    )

    return f"""
<style>{ESTILO}</style>
<h1>Pacientes ativos sem consulta marcada</h1>
<p class="sub">Posição de {dia} · {len(separacao.a_agendar)} para agendar ·
{len(separacao.conferir)} a conferir ·
{len(separacao.ja_agendados)} já na agenda</p>
{bloco_aviso}

<h2>Agendar — {len(separacao.a_agendar)} pacientes</h2>
<p class="leve">Ordenados por quanto falta para o plano vencer.</p>
{_tabela(separacao.a_agendar)}

<h2>Conferir antes de chamar — {len(separacao.conferir)}</h2>
<p class="leve">O nome bate parcialmente com alguém da agenda.
Confirme quem é antes de mandar mensagem.</p>
{_tabela(separacao.conferir)}

<h2>Já têm consulta marcada — {len(separacao.ja_agendados)}</h2>
<ul>{agendados or "<li class='vazio'>Ninguém.</li>"}</ul>

<h2>Aparecem na agenda de outro profissional — {len(separacao.de_outro_profissional)}</h2>
<ul>{outros or "<li class='vazio'>Ninguém.</li>"}</ul>
"""
