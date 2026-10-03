#!/usr/bin/env python3
"""Valida produtos.json: campos obrigatórios, duplicatas e coerência calórica."""
import json
import sys
from pathlib import Path

OBRIG = ["nome", "marca", "categoria", "porcao_g", "kcal", "proteina_g", "fibra_g", "papel", "fonte", "preparo", "viagem_aviao", "viagem_carro"]


def main():
    prods = json.loads((Path(__file__).parent / "produtos.json").read_text(encoding="utf-8"))["produtos"]
    erros, avisos, vistos = [], [], set()
    for p in prods:
        nome = f"{p.get('nome')} ({p.get('marca')})"
        if nome in vistos:
            erros.append(f"duplicado: {nome}")
        vistos.add(nome)
        for c in OBRIG:
            if c not in p:
                erros.append(f"{nome}: falta '{c}'")
        if p.get("proteina_g", 0) * 4 > p.get("kcal", 0) * 1.05 + 1:
            erros.append(f"{nome}: proteína*4 ({p['proteina_g'] * 4}) maior que kcal ({p['kcal']})")
        if None not in (p.get("carbo_g"), p.get("gordura_g")):
            calc = 4 * p["proteina_g"] + 4 * p["carbo_g"] + 9 * p["gordura_g"]
            if abs(calc - p["kcal"]) > max(25, p["kcal"] * 0.3):
                avisos.append(f"{nome}: kcal declarada {p['kcal']} vs macros {calc:.0f}")
        if p.get("fonte", "").startswith("estimado"):
            avisos.append(f"{nome}: valores estimados, buscar rótulo")
    for a in avisos:
        print("AVISO", a)
    for e in erros:
        print("ERRO ", e)
    print(f"\n{len(prods)} produtos, {len(erros)} erros, {len(avisos)} avisos")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
