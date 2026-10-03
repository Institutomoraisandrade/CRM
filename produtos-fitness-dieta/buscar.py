#!/usr/bin/env python3
"""Ranqueia produtos fitness para dieta (foco em emagrecimento).

Uso:
  python buscar.py                      # ranking geral
  python buscar.py --categoria "whey isolado"
  python buscar.py --max-kcal 120 --min-proteina 20
"""
import argparse
import json
from pathlib import Path


def carregar():
    return json.loads((Path(__file__).parent / "produtos.json").read_text(encoding="utf-8"))["produtos"]


def enriquecer(p):
    p["prot_por_100kcal"] = round(p["proteina_g"] / p["kcal"] * 100, 1)
    p["pct_kcal_proteina"] = round(p["proteina_g"] * 4 / p["kcal"] * 100)
    if p.get("preco_brl") and p.get("rendimento_porcoes"):
        p["rs_por_g_proteina"] = round(p["preco_brl"] / p["rendimento_porcoes"] / p["proteina_g"], 2)
    return p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--categoria")
    ap.add_argument("--max-kcal", type=float)
    ap.add_argument("--min-proteina", type=float)
    a = ap.parse_args()

    itens = [enriquecer(p) for p in carregar()]
    if a.categoria:
        itens = [p for p in itens if p["categoria"].lower() == a.categoria.lower()]
    if a.max_kcal:
        itens = [p for p in itens if p["kcal"] <= a.max_kcal]
    if a.min_proteina:
        itens = [p for p in itens if p["proteina_g"] >= a.min_proteina]
    itens.sort(key=lambda p: (-p["prot_por_100kcal"], p["gordura_g"]))

    print(f"{'#':<3}{'Produto':<34}{'Porção':>7}{'kcal':>6}{'Prot':>6}{'P/100kcal':>10}{'%kcal prot':>11}")
    for i, p in enumerate(itens, 1):
        nome = f"{p['nome']} ({p['marca']})"[:33]
        print(f"{i:<3}{nome:<34}{p['porcao_g']:>6}g{p['kcal']:>6}{p['proteina_g']:>5}g{p['prot_por_100kcal']:>10}{p['pct_kcal_proteina']:>10}%")
    print("\nValores aproximados; confira o rótulo. Não substitui orientação de nutricionista.")


if __name__ == "__main__":
    main()
