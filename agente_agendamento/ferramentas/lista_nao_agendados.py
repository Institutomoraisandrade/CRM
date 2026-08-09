"""Monta o PDF dos pacientes ativos que ainda não têm consulta marcada.

Come três coisas:

* a exportação de pacientes do LiveClin (CSV);
* os eventos da sua agenda, como o Google Calendar devolve (JSON);
* opcionalmente, os eventos da agenda de outro profissional, para tirar
  da fila quem é paciente dele.

Uso:

    python3 ferramentas/lista_nao_agendados.py \\
        --pacientes exportacao.csv \\
        --agenda agenda_daniel.json \\
        --outra-agenda agenda_juliana.json \\
        --saida nao_agendados.pdf

O JSON da agenda pode ser a resposta crua da API (``{"events": [...]}``)
ou só a lista de eventos.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agente.entrega.pdf import ErroDePDF, html_para_pdf  # noqa: E402
from agente.nao_agendados import (  # noqa: E402
    Pendencia,
    ler_agenda,
    montar_html,
    nome_do_evento,
    separar,
)

# Como a exportação nomeia as colunas.
COLUNA = {
    "nome": "patientReport.headers.full_name",
    "status": "patientReport.headers.customer_status",
    "telefone": "patientReport.headers.phone_number",
    "plano": "patientReport.headers.last_service_provided",
    "fim": "patientReport.headers.service_end_date",
    "restam": "patientReport.headers.service_days_remaining",
}


def eventos_de(caminho: Path) -> list[dict]:
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    return dados["events"] if isinstance(dados, dict) else dados


def telefone(bruto: str) -> str:
    digitos = "".join(c for c in bruto if c.isdigit())
    return digitos


def pacientes_ativos(caminho: Path) -> list[Pendencia]:
    with caminho.open(encoding="utf-8-sig") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    fila = []
    for linha in linhas:
        if linha.get(COLUNA["status"], "").strip().lower() != "active":
            continue
        try:
            restam = int(linha.get(COLUNA["restam"]) or 0)
        except ValueError:
            restam = 0
        fila.append(
            Pendencia(
                nome=linha[COLUNA["nome"]].strip(),
                plano=(linha.get(COLUNA["plano"]) or "—").strip(),
                fim_do_plano=(linha.get(COLUNA["fim"]) or "—").strip(),
                dias_restantes=restam,
                whatsapp=telefone(linha.get(COLUNA["telefone"]) or ""),
            )
        )
    return fila


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__)
    analisador.add_argument("--pacientes", required=True, type=Path)
    analisador.add_argument("--agenda", required=True, type=Path)
    analisador.add_argument("--outra-agenda", type=Path)
    analisador.add_argument("--saida", type=Path, default=Path("nao_agendados.pdf"))
    analisador.add_argument("--hoje", type=date.fromisoformat, default=date.today())
    analisador.add_argument("--aviso", default="")
    opcoes = analisador.parse_args(argv)

    fila = pacientes_ativos(opcoes.pacientes)
    agenda = ler_agenda(eventos_de(opcoes.agenda), opcoes.hoje)

    de_outro: set[str] = set()
    if opcoes.outra_agenda:
        for evento in eventos_de(opcoes.outra_agenda):
            nome = nome_do_evento((evento.get("summary") or "").strip())
            if nome:
                de_outro.add(nome)

    separacao = separar(fila, agenda, de_outro)
    html = montar_html(separacao, opcoes.hoje, opcoes.aviso)

    destino = opcoes.saida
    if destino.suffix.lower() == ".pdf":
        try:
            html_para_pdf(html, destino, "Pacientes sem consulta marcada")
        except ErroDePDF as erro:
            print(erro, file=sys.stderr)
            return 1
    else:
        destino.write_text(html, encoding="utf-8")

    print(
        f"{len(separacao.a_agendar)} para agendar, "
        f"{len(separacao.conferir)} a conferir, "
        f"{len(separacao.ja_agendados)} já na agenda, "
        f"{len(separacao.de_outro_profissional)} de outro profissional."
    )
    print(f"Gravado em {destino.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
