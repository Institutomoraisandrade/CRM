#!/usr/bin/env python3
"""Une as referências produzidas pelos subagentes (02 e 03) em um único
referencias.json, removendo duplicatas por DOI, PMID ou título.

Uso:
  python3 mesclar_referencias.py saida.json entrada1.json entrada2.json [...]

Quando a mesma obra aparece com ids diferentes, o primeiro id é mantido e os
demais entram em "aliases" — assim citações [@id_antigo] continuam funcionando.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abnt  # noqa: E402


def chaves(r: dict) -> list[str]:
    out = []
    if r.get("doi"):
        out.append("doi:" + re.sub(r"^https?://(dx\.)?doi\.org/", "", r["doi"].strip().lower()))
    if r.get("pmid"):
        out.append("pmid:" + str(r["pmid"]).strip())
    if r.get("titulo"):
        t = re.sub(r"[^a-z0-9]", "", abnt.sem_acento(r["titulo"]).lower())
        out.append(f"tit:{t}:{r.get('ano')}")
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    saida = Path(sys.argv[1])
    unidas: list[dict] = []
    indice: dict[str, dict] = {}
    ids_usados: set[str] = set()
    for arq in sys.argv[2:]:
        p = Path(arq)
        if not p.exists():
            print(f"aviso: {arq} não existe, ignorado")
            continue
        for r in abnt.carregar_referencias(p):
            existente = next((indice[k] for k in chaves(r) if k in indice), None)
            if existente:
                if r["id"] != existente["id"]:
                    existente.setdefault("aliases", [])
                    if r["id"] not in existente["aliases"]:
                        existente["aliases"].append(r["id"])
                for campo, valor in r.items():  # completa campos vazios
                    if campo not in ("id", "aliases") and valor and not existente.get(campo):
                        existente[campo] = valor
                if r.get("verificado") and not existente.get("verificado"):
                    existente["verificado"] = True
                    existente["verificado_via"] = r.get("verificado_via")
                continue
            if r["id"] in ids_usados:
                novo = r["id"] + "b"
                print(f"aviso: id '{r['id']}' já usado por outra obra em {arq}; renomeado para '{novo}'")
                r["id"] = novo
            ids_usados.add(r["id"])
            unidas.append(r)
            for k in chaves(r):
                indice[k] = r
    saida.write_text(json.dumps(unidas, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    nao_verif = [r["id"] for r in unidas if not r.get("verificado")]
    print(f"{len(unidas)} referência(s) únicas gravadas em {saida}")
    if nao_verif:
        print(f"ATENÇÃO: {len(nao_verif)} sem verificação (verificado != true): {', '.join(nao_verif)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
