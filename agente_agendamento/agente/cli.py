"""Interface de linha de comando do agente."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime

from .agenda.base import ErroDeAgenda
from .config import Config, ErroDeConfig, carregar_config
from .fontes.base import ErroDeFonte
from .modelos import Agendamento, Paciente, SituacaoAgendamento, StatusPaciente
from .notificacoes import gravar, montar_notificacoes
from .regras import INTERVALO_MAXIMO_DIAS, data_limite_retorno, etiqueta_vigencia

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


def _planejar(args: argparse.Namespace) -> tuple[Config, list[Paciente], list[Agendamento]]:
    config, pacientes = _carregar(args.config)
    agendador = config.construir_agendador()
    agendamentos = agendador.planejar(pacientes)
    return config, pacientes, agendamentos


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
    config, pacientes, agendamentos = _planejar(args)
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
    config, pacientes, agendamentos = _planejar(args)
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
    config, pacientes, agendamentos = _planejar(args)
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (ErroDeConfig, ErroDeFonte, ErroDeAgenda) as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
