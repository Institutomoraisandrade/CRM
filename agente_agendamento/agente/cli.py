"""Interface de linha de comando do agente."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, datetime

from . import filtros
from .agenda.base import ErroDeAgenda
from .config import Config, ErroDeConfig, carregar_config
from .consultas import aplicar_ultima_consulta, cruzar
from .entrega.email import ErroDeEnvio
from .entrega.pdf import ErroDePDF, html_para_pdf
from .fontes.base import ErroDeFonte
from .inativos import RelatorioInativos, levantar
from .modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from .notificacoes import alertas_pendentes, gravar, montar_notificacoes
from .regras import INTERVALO_MAXIMO_DIAS, data_limite_retorno, etiqueta_vigencia
from .relatorio import montar

CONFIG_PADRAO = "config.toml"


def _carregar(caminho: str) -> tuple[Config, list[Paciente]]:
    config = carregar_config(caminho)
    fonte = config.construir_fonte()
    pacientes = fonte.carregar()
    for aviso in fonte.avisos:
        print(f"  aviso: {aviso}", file=sys.stderr)
    return config, pacientes


def _linha(colunas: list[str], larguras: list[int]) -> str:
    return "  ".join(texto.ljust(largura)[:largura] for texto, largura in zip(colunas, larguras))


def comando_verificar(args: argparse.Namespace) -> int:
    config, pacientes = _carregar(args.config)
    hoje = date.today()

    print(f"Planilha: {config.caminho_relativo(config.fonte.get('caminho', ''))}")
    print(f"Pacientes lidos: {len(pacientes)}")

    por_status = {s: 0 for s in StatusPaciente}
    for paciente in pacientes:
        por_status[paciente.status] += 1
    print(
        "  ativos: {ativo}  pausados: {pausado}  inativos: {inativo}".format(
            ativo=por_status[StatusPaciente.ATIVO],
            pausado=por_status[StatusPaciente.PAUSADO],
            inativo=por_status[StatusPaciente.INATIVO],
        )
    )

    larguras = [28, 12, 12, 12, 18]
    print()
    print(_linha(["PACIENTE", "PLANO", "FIM PLANO", "LIMITE 30D", "ETIQUETA"], larguras))
    for paciente in sorted(pacientes, key=lambda p: data_limite_retorno(p)):
        if paciente.status is not StatusPaciente.ATIVO:
            continue
        print(
            _linha(
                [
                    paciente.nome,
                    paciente.plano.nome,
                    f"{paciente.plano_fim:%d/%m/%Y}",
                    f"{data_limite_retorno(paciente):%d/%m/%Y}",
                    etiqueta_vigencia(paciente, hoje),
                ],
                larguras,
            )
        )
    return 0


def _imprimir_plano(agendamentos: list[Agendamento]) -> None:
    larguras = [28, 18, 12, 14]
    print(_linha(["PACIENTE", "RETORNO", "LIMITE 30D", "SITUAÇÃO"], larguras))
    for item in agendamentos:
        if item.situacao is SituacaoAgendamento.IGNORADO:
            continue
        quando = f"{item.inicio:%d/%m/%Y %H:%M}" if item.inicio else "—"
        limite = f"{item.limite:%d/%m/%Y}" if item.limite else "—"
        print(_linha([item.paciente.nome, quando, limite, item.situacao.value], larguras))
        if item.motivo:
            print(f"      {item.motivo}")


def _planejar(
    args: argparse.Namespace,
) -> tuple[Config, list[Paciente], list[Agendamento], object | None]:
    """Pipeline completo: LiveClin, WebDiet e então o agendamento.

    O WebDiet vem antes do agendador de propósito: é dele que sai a data
    da última consulta, e é ela que define o limite de 30 dias.
    """
    config, pacientes = _carregar(args.config)
    hoje = date.today()

    cruzamento = _cruzar_webdiet(config, pacientes, hoje)
    if cruzamento is not None:
        for ajuste in aplicar_ultima_consulta(cruzamento):
            print(f"  webdiet: {ajuste}", file=sys.stderr)

    agendador = config.construir_agendador()
    agendamentos = agendador.planejar(pacientes)
    return config, pacientes, agendamentos, cruzamento


def _validar_invariante(agendamentos: list[Agendamento]) -> None:
    """Nenhuma proposta pode passar do limite de 30 dias nem da vigência."""
    for item in agendamentos:
        if item.inicio is None:
            continue
        dia = item.inicio.date()
        if dia > item.paciente.plano_fim:
            raise AssertionError(
                f"{item.paciente.nome}: retorno {dia} passa do fim do plano "
                f"{item.paciente.plano_fim}"
            )
        if item.situacao is SituacaoAgendamento.AGENDAVEL and item.limite and dia > item.limite:
            raise AssertionError(
                f"{item.paciente.nome}: retorno {dia} passa do limite de "
                f"{INTERVALO_MAXIMO_DIAS} dias ({item.limite})"
            )


def comando_planejar(args: argparse.Namespace) -> int:
    config, pacientes, agendamentos, _ = _planejar(args)
    _validar_invariante(agendamentos)
    _imprimir_plano(agendamentos)

    destino = config.caminho_relativo(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(
            {
                "gerado_em": datetime.now().isoformat(timespec="seconds"),
                "limite_dias": INTERVALO_MAXIMO_DIAS,
                "agendamentos": [
                    {
                        "paciente": a.paciente.nome,
                        "whatsapp": a.paciente.whatsapp,
                        "plano": a.paciente.plano.nome,
                        "situacao": a.situacao.value,
                        "limite": a.limite.isoformat() if a.limite else None,
                        "inicio": a.inicio.isoformat() if a.inicio else None,
                        "fim": a.fim.isoformat() if a.fim else None,
                        "motivo": a.motivo,
                    }
                    for a in agendamentos
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nPlano gravado em {destino} (nada foi criado na agenda).")
    print("Para efetivar: python -m agente aplicar --confirmar")
    return 0


def comando_aplicar(args: argparse.Namespace) -> int:
    config, pacientes, agendamentos, _ = _planejar(args)
    _validar_invariante(agendamentos)
    _imprimir_plano(agendamentos)

    marcaveis = [
        a
        for a in agendamentos
        if a.inicio is not None
        and a.situacao in (SituacaoAgendamento.AGENDAVEL, SituacaoAgendamento.ATRASADO)
    ]
    if not marcaveis:
        print("\nNada para marcar.")
        return 0

    if not args.confirmar:
        print(
            f"\n{len(marcaveis)} consulta(s) prontas para entrar na agenda. "
            "Rode de novo com --confirmar para criar de verdade."
        )
        return 0

    agenda = config.construir_agenda()
    criados = 0
    for item in marcaveis:
        assert item.inicio is not None and item.fim is not None
        titulo = f"Consulta — {item.paciente.nome}"
        descricao = (
            f"Plano: {item.paciente.plano.nome}\n"
            f"Vigência até: {item.paciente.plano_fim:%d/%m/%Y}\n"
            f"Limite de {INTERVALO_MAXIMO_DIAS} dias: "
            f"{item.limite:%d/%m/%Y}\n"
            f"Agendado pelo agente em {date.today():%d/%m/%Y}"
        )
        identificador = agenda.criar_evento(titulo, item.inicio, item.fim, descricao)
        criados += 1
        print(f"  criado: {item.paciente.nome} em {item.inicio:%d/%m/%Y %H:%M} ({identificador})")

    print(f"\n{criados} consulta(s) criada(s) na agenda.")
    return 0


def comando_alertas(args: argparse.Namespace) -> int:
    config, pacientes, agendamentos, _ = _planejar(args)
    fila = montar_notificacoes(pacientes, agendamentos)

    if not fila:
        print("Nenhum alerta para hoje.")
        return 0

    for notificacao in fila:
        marca = "whatsapp" if notificacao.canal == "whatsapp" else "sistema "
        print(f"[{marca}] {notificacao.paciente}: {notificacao.mensagem}")

    caminho = config.notificacoes.get("arquivo", "notificacoes.json")
    destino = gravar(fila, config.caminho_relativo(caminho))
    pendentes_whatsapp = sum(1 for n in fila if n.canal == "whatsapp")
    print(f"\n{len(fila)} notificação(ões) gravadas em {destino}.")
    print(
        f"{pendentes_whatsapp} mensagem(ns) de WhatsApp ficaram preparadas, "
        "sem envio (nenhuma API conectada)."
    )
    return 0


def _etiquetas(args: argparse.Namespace, config: Config) -> list[str]:
    """Etiquetas a considerar: da linha de comando ou do config.toml."""
    if args.etiqueta:
        return list(args.etiqueta)
    configuradas = config.filtro.get("etiquetas") or config.filtro.get("etiqueta")
    if isinstance(configuradas, str):
        configuradas = [configuradas]
    return [e for e in (configuradas or []) if e and e.strip()]


def _cruzar_webdiet(config: Config, pacientes: list[Paciente], hoje: date):
    """Cruza com as avaliações do WebDiet, se a fonte estiver configurada."""
    fonte = config.construir_fonte_webdiet()
    if fonte is None:
        print(
            "  aviso: [webdiet] não configurado — o relatório sai sem a contagem "
            "de consultas.",
            file=sys.stderr,
        )
        return None
    avaliacoes = fonte.carregar()
    for aviso in fonte.avisos:
        print(f"  aviso: {aviso}", file=sys.stderr)
    resultado = cruzar(pacientes, avaliacoes, hoje)
    for aviso in resultado.avisos:
        print(f"  nomes: {aviso}", file=sys.stderr)
    return resultado


def comando_relatorio(args: argparse.Namespace) -> int:
    config, todos, agendamentos_todos, cruzamento = _planejar(args)
    _validar_invariante(agendamentos_todos)

    hoje = date.today()
    etiquetas = _etiquetas(args, config)
    incluir_inativos = args.incluir_inativos or bool(config.filtro.get("incluir_inativos"))

    pacientes = filtros.aplicar(
        todos, etiquetas=etiquetas, somente_ativos=not incluir_inativos
    )
    if not pacientes:
        alvo = f" com as etiquetas {', '.join(etiquetas)}" if etiquetas else ""
        print(f"Nenhum paciente ativo{alvo} na planilha.", file=sys.stderr)
        return 1

    selecionados = {p.nome for p in pacientes}
    agendamentos = [a for a in agendamentos_todos if a.paciente.nome in selecionados]

    relatorio = montar(
        pacientes,
        agendamentos,
        alertas_pendentes(pacientes, hoje),
        hoje,
        cruzamento=cruzamento,
        titulo_filtro=filtros.descrever(etiquetas, not incluir_inativos),
    )

    print(relatorio.texto())

    destino = config.caminho_relativo(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(relatorio.html(), encoding="utf-8")
    print(f"\nPrévia gravada em {destino}")

    anexos = _gerar_pdf(config, relatorio, args, destino)

    if not args.enviar:
        print("Para enviar por e-mail: python -m agente relatorio --enviar")
        return 0

    enviador = config.construir_enviador()
    entregues = enviador.enviar(
        relatorio.assunto, relatorio.texto(), relatorio.html(), anexos
    )
    extra = f" com {len(anexos)} anexo(s)" if anexos else ""
    print(f"E-mail enviado para {', '.join(entregues)}{extra}.")
    return 0


def _gerar_pdf(config: Config, relatorio, args, origem_html) -> list:
    """Gera o PDF quando pedido; a falta do Chrome não derruba o relatório."""
    if getattr(args, "sem_pdf", False):
        return []
    caminho = config.caminho_relativo(
        getattr(args, "pdf", None) or origem_html.with_suffix(".pdf").name
    )
    try:
        gerado = html_para_pdf(relatorio.html(), caminho, relatorio.assunto)
    except ErroDePDF as erro:
        print(f"  aviso: PDF não gerado — {erro}", file=sys.stderr)
        return []
    print(f"PDF gravado em {gerado}")
    return [gerado]


def comando_inativos(args: argparse.Namespace) -> int:
    config, todos, _, cruzamento = _planejar(args)
    hoje = date.today()

    etiquetas = _etiquetas(args, config)
    # Aqui o filtro de status não se aplica: o alvo são justamente os que
    # não estão ativos.
    candidatos = filtros.aplicar(todos, etiquetas=etiquetas, somente_ativos=False)
    parados = levantar(candidatos, hoje, cruzamento)

    relatorio = RelatorioInativos(parados, hoje)
    print(relatorio.texto())

    destino = config.caminho_relativo(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(relatorio.html(), encoding="utf-8")
    print(f"\nPrévia gravada em {destino}")

    anexos = _gerar_pdf(config, relatorio, args, destino)

    if not args.enviar:
        print("Para enviar por e-mail: python -m agente inativos --enviar")
        return 0

    enviador = config.construir_enviador()
    entregues = enviador.enviar(
        relatorio.assunto, relatorio.texto(), relatorio.html(), anexos
    )
    print(f"E-mail enviado para {', '.join(entregues)}.")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agente",
        description=(
            "Agente local de agendamento de pacientes. Lê os planos exportados do "
            f"LiveClin e marca os retornos dentro do limite de {INTERVALO_MAXIMO_DIAS} dias."
        ),
    )
    parser.add_argument(
        "--config", default=CONFIG_PADRAO, help=f"arquivo de configuração (padrão: {CONFIG_PADRAO})"
    )
    subcomandos = parser.add_subparsers(dest="comando", required=True)

    verificar = subcomandos.add_parser(
        "verificar", help="lê a planilha e mostra os planos e etiquetas"
    )
    verificar.set_defaults(func=comando_verificar)

    planejar = subcomandos.add_parser(
        "planejar", help="calcula os retornos sem tocar na agenda"
    )
    planejar.add_argument("--saida", default="plano_de_agendamento.json")
    planejar.set_defaults(func=comando_planejar)

    aplicar = subcomandos.add_parser("aplicar", help="cria as consultas na agenda")
    aplicar.add_argument(
        "--confirmar", action="store_true", help="efetiva a criação dos compromissos"
    )
    aplicar.set_defaults(func=comando_aplicar)

    alertas = subcomandos.add_parser(
        "alertas", help="lista os avisos de check-in e de vencimento de plano"
    )
    alertas.set_defaults(func=comando_alertas)

    relatorio = subcomandos.add_parser(
        "relatorio", help="monta o resumo do dia e envia para o seu e-mail"
    )
    relatorio.add_argument(
        "--enviar", action="store_true", help="envia o e-mail de verdade"
    )
    relatorio.add_argument(
        "--etiqueta",
        action="append",
        default=None,
        help=(
            "considera apenas pacientes com esta etiqueta; repita para incluir "
            "mais de uma (ex.: --etiqueta \"Ativos - Daniel\" "
            "--etiqueta \"Ativos - Juliana\")"
        ),
    )
    relatorio.add_argument(
        "--incluir-inativos",
        action="store_true",
        help="inclui pausados e inativos (por padrão só entram os ativos)",
    )
    relatorio.add_argument("--saida", default="relatorio.html")
    relatorio.add_argument("--pdf", default=None, help="caminho do PDF gerado")
    relatorio.add_argument(
        "--sem-pdf", action="store_true", help="não gera o PDF"
    )
    relatorio.set_defaults(func=comando_relatorio)

    inativos = subcomandos.add_parser(
        "inativos",
        help="lista quem parou e há quanto tempo, e envia por e-mail",
    )
    inativos.add_argument(
        "--enviar", action="store_true", help="envia o e-mail de verdade"
    )
    inativos.add_argument(
        "--etiqueta", action="append", default=None, help="filtra por etiqueta"
    )
    inativos.add_argument("--saida", default="inativos.html")
    inativos.add_argument("--pdf", default=None)
    inativos.add_argument("--sem-pdf", action="store_true")
    inativos.set_defaults(func=comando_inativos)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ErroDeConfig, ErroDeFonte, ErroDeAgenda, ErroDeEnvio, ErroDePDF) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
