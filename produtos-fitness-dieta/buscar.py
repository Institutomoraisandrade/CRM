#!/usr/bin/env python3
"""Ranqueia produtos fitness para dieta (foco em emagrecimento).

Modos de ordenação (--por):
  proteina   proteína por 100 kcal (padrão)
  saciedade  menor densidade calórica (kcal/g) e mais fibra
  lanche     menos kcal por porção, desempate por proteína

Exemplos:
  python buscar.py
  python buscar.py --por saciedade
  python buscar.py --papel lanche --por lanche
  python buscar.py --categoria "snack crocante" --max-kcal 120
"""
import argparse
import json
from pathlib import Path


def carregar():
    return json.loads((Path(__file__).parent / "produtos.json").read_text(encoding="utf-8"))["produtos"]


def enriquecer(p):
    p["prot_100kcal"] = round(p["proteina_g"] / max(p["kcal"], 1) * 100, 1)
    p["kcal_por_g"] = round(p["kcal"] / p["porcao_g"], 2)
    if p.get("preco_brl") and p.get("rendimento_porcoes"):
        p["rs_por_g_proteina"] = round(p["preco_brl"] / p["rendimento_porcoes"] / p["proteina_g"], 2)
    return p


CHAVES = {
    "proteina": lambda p: (-p["prot_100kcal"], p["gordura_g"]),
    "saciedade": lambda p: (p["kcal_por_g"], -p["fibra_g"]),
    "lanche": lambda p: (p["kcal"], -p["proteina_g"]),
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--por", choices=CHAVES, default="proteina")
    ap.add_argument("--papel", help="proteina | lanche | base | gordura")
    ap.add_argument("--categoria")
    ap.add_argument("--preparo", choices=["pronto", "minimo"], help="pronto = abrir e comer")
    ap.add_argument("--markdown", action="store_true", help="saída em tabela Markdown")
    ap.add_argument("--max-kcal", type=float)
    ap.add_argument("--min-proteina", type=float)
    a = ap.parse_args()

    itens = [enriquecer(p) for p in carregar()]
    if a.papel:
        itens = [p for p in itens if p["papel"] == a.papel]
    if a.preparo:
        itens = [p for p in itens if p["preparo"] == a.preparo]
    if a.categoria:
        itens = [p for p in itens if p["categoria"].lower() == a.categoria.lower()]
    if a.max_kcal:
        itens = [p for p in itens if p["kcal"] <= a.max_kcal]
    if a.min_proteina:
        itens = [p for p in itens if p["proteina_g"] >= a.min_proteina]
    itens.sort(key=CHAVES[a.por])

    if a.markdown:
        print("| # | Produto | Categoria | Porção | kcal | Prot (g) | Fibra (g) | Prot/100kcal | Como usar |")
        print("|--:|---|---|--:|--:|--:|--:|--:|---|")
        for i, p in enumerate(itens, 1):
            fib = "-" if p["fibra_g"] is None else p["fibra_g"]
            print(f"| {i} | {p['nome']} ({p['marca']}) | {p['categoria']} | {p['porcao_g']} g | {p['kcal']} | {p['proteina_g']} | {fib} | {p['prot_100kcal']} | {p.get('obs', '')} |")
        return
    print(f"{'#':<3}{'Produto':<44}{'Porção':>7}{'kcal':>6}{'Prot':>6}{'Fibra':>6}{'P/100kcal':>10}{'kcal/g':>8}")
    for i, p in enumerate(itens, 1):
        nome = f"{p['nome']} ({p['marca']})"[:43]
        print(f"{i:<3}{nome:<44}{p['porcao_g']:>6}g{p['kcal']:>6}{p['proteina_g']:>5}g{(p['fibra_g'] or 0):>5}g{p['prot_100kcal']:>10}{p['kcal_por_g']:>8}")
    print("\nValores aproximados; confira o rótulo. Não substitui orientação de nutricionista.")


if __name__ == "__main__":
    main()
