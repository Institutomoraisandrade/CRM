#!/usr/bin/env python3
"""Confere referências contra metadados obtidos no PubMed (camada operacional).

O subagente verificador (Haiku) busca os metadados com mcp__PubMed__get_article_metadata,
grava um JSON compacto e este script faz a comparação campo a campo — sem julgamento
subjetivo. Divergências ambíguas ficam para o líder (Opus) decidir.

Formato de entrada dos metadados (verificacao/pubmed.json):
  {"33782057": {"titulo": "...", "ano": "2021", "volume": "372", "numero": null,
                "paginas": "n71", "doi": "10.1136/bmj.n71", "periodico": "BMJ",
                "autores": ["Page", "McKenzie", "Bossuyt"]}}

Uso:
  python3 conferir_referencias.py --pendentes refs.json
      → lista, pronta para mcp__PubMed__lookup_article_by_citation, as referências de artigo sem PMID
  python3 conferir_referencias.py refs.json verificacao/pubmed.json [--corrigir] [-o relatorio.json]

--corrigir aplica correções seguras (ano, volume, número, páginas, DOI) quando título e
primeiro autor batem, e marca "verificado": true com "verificado_via": "PubMed PMID ...".
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path


def norm(s) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", str(s or "").lower())
                if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def expandir_paginas(p) -> str:
    """'924-6' -> '924-926'; 'E839-42' -> 'E839-E842'."""
    p = str(p or "").strip().replace("–", "-")
    m = re.fullmatch(r"([A-Za-z]?)(\d+)-([A-Za-z]?)(\d+)", p)
    if not m:
        return p
    pre1, ini, pre2, fim = m.groups()
    if len(fim) < len(ini):
        fim = ini[: len(ini) - len(fim)] + fim
    return f"{pre1}{ini}-{pre1 or pre2}{fim}"


def titulo_ref(r: dict) -> str:
    t = r.get("titulo") or ""
    if r.get("subtitulo"):
        t += ": " + r["subtitulo"]
    return t


def sobrenome(autor: str) -> str:
    autor = autor.strip()
    return autor.split(",")[0] if "," in autor else autor.split(" ")[-1]


def conferir(r: dict, meta: dict) -> dict:
    res = {"id": r["id"], "pmid": r.get("pmid"), "status": "ok", "divergencias": [], "correcoes": {}}
    sim = difflib.SequenceMatcher(None, norm(titulo_ref(r)), norm(meta.get("titulo"))).ratio()
    res["similaridade_titulo"] = round(sim, 2)
    if sim < 0.85:
        res["divergencias"].append(f"título difere (similaridade {sim:.2f}): PubMed = \"{meta.get('titulo')}\"")
    autores_pm = [norm(a) for a in meta.get("autores") or []]
    if r.get("autores") and autores_pm:
        s_ref = norm(sobrenome(r["autores"][0]))
        if not (s_ref in autores_pm[0] or autores_pm[0] in s_ref
                or any(s_ref and s_ref in a for a in autores_pm[:1])):
            res["divergencias"].append(f"1º autor difere: ref = {r['autores'][0]!r}, PubMed = {meta['autores'][0]!r}")
        if len(meta["autores"]) > 4 and not r.get("et_al") and len(r["autores"]) < len(meta["autores"]):
            res["correcoes"]["et_al"] = True
    for campo in ("ano", "volume", "numero", "paginas", "doi"):
        v_meta = meta.get(campo)
        if v_meta in (None, ""):
            continue
        v_ref = r.get(campo)
        a, b = str(v_ref or "").strip(), str(v_meta).strip()
        if campo == "paginas":
            a, b = expandir_paginas(a), expandir_paginas(b)
        if campo == "doi":
            a, b = a.lower().replace("https://doi.org/", ""), b.lower()
        if a != b:
            if v_ref in (None, ""):
                res["correcoes"][campo] = b if campo != "ano" else int(b)
            elif campo == "ano" and a.isdigit() and b.isdigit() and 0 < int(a) - int(b) <= 3:
                # PubMed com ano ANTERIOR ao da referência (até 3 anos) costuma ser publicação eletrônica
                # antecipada × fascículo impresso.
                # A ABNT usa o ano do fascículo: não corrigir automaticamente — o líder confere.
                res["divergencias"].append(
                    f"ano: ref = {v_ref!r}, PubMed = {v_meta!r} (possível epub antecipado; conferir o ano do fascículo)")
                res["ano_a_conferir"] = True
            else:
                res["divergencias"].append(f"{campo}: ref = {v_ref!r}, PubMed = {v_meta!r}")
                res["correcoes"][campo] = b if campo != "ano" else int(b)
    titulo_ok = sim >= 0.85
    autor_ok = not any(d.startswith("1º autor") for d in res["divergencias"])
    if not (titulo_ok and autor_ok) or res.get("ano_a_conferir"):
        res["status"] = "revisar"     # identidade ou ano duvidosos: decisão do líder
    elif res["divergencias"]:
        res["status"] = "corrigivel"  # mesma obra, metadados a ajustar
    return res


def pendentes(refs: list[dict]) -> list[dict]:
    """Monta as consultas de citação para artigos sem PMID (passo 1 do verificador)."""
    out = []
    for r in refs:
        if r.get("pmid") or (r.get("tipo") or "artigo") != "artigo":
            continue
        cit = {"key": r["id"]}
        if r.get("periodico"):
            cit["journal"] = r["periodico"]
        if str(r.get("ano", "")).isdigit():
            cit["year"] = int(r["ano"])
        if r.get("volume"):
            cit["volume"] = str(r["volume"])
        pg = str(r.get("paginas") or "")
        m = re.match(r"[A-Za-z]?\d+", pg)
        if m:
            cit["first_page"] = m.group(0)
        if r.get("autores"):
            cit["author"] = sobrenome(r["autores"][0])
        out.append({"id": r["id"], "citacao": cit,
                    "busca_por_titulo": f"\"{titulo_ref(r)}\"[Title]" if r.get("titulo") else None})
    return out


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--pendentes":
        refs = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        lst = pendentes(refs)
        print(json.dumps({"citations": [x["citacao"] for x in lst],
                          "buscas_por_titulo": {x["id"]: x["busca_por_titulo"] for x in lst}},
                         ensure_ascii=False, indent=2))
        print(f"{len(lst)} artigo(s) sem PMID", file=sys.stderr)
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("refs", type=Path)
    ap.add_argument("metadados", type=Path)
    ap.add_argument("--corrigir", action="store_true")
    ap.add_argument("-o", "--relatorio", type=Path)
    a = ap.parse_args()
    refs = json.loads(a.refs.read_text(encoding="utf-8"))
    metas = json.loads(a.metadados.read_text(encoding="utf-8"))
    relatorio = []
    for r in refs:
        pmid = str(r.get("pmid") or "").strip()
        if not pmid:
            relatorio.append({"id": r["id"], "status": "sem_pmid",
                              "nota": "confirmar por DOI/site oficial (diretriz, livro, documento)"})
            continue
        if pmid not in metas:
            relatorio.append({"id": r["id"], "pmid": pmid, "status": "sem_metadados",
                              "nota": "PMID não consultado ou inexistente"})
            continue
        res = conferir(r, metas[pmid])
        if a.corrigir and res["status"] in ("ok", "corrigivel"):
            r.update(res["correcoes"])
            r["verificado"] = True
            r["verificado_via"] = f"PubMed PMID {pmid}"
            res["aplicado"] = bool(res["correcoes"])
        relatorio.append(res)
    if a.corrigir:
        a.refs.write_text(json.dumps(refs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resumo = {s: sum(1 for x in relatorio if x["status"] == s)
              for s in ("ok", "corrigivel", "revisar", "sem_pmid", "sem_metadados")}
    saida = {"arquivo": str(a.refs), "resumo": resumo, "itens": relatorio}
    if a.relatorio:
        a.relatorio.parent.mkdir(parents=True, exist_ok=True)
        a.relatorio.write_text(json.dumps(saida, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False))
    for x in relatorio:
        if x["status"] != "ok":
            print(f"  [{x['status']}] {x['id']}: " + "; ".join(x.get("divergencias") or [x.get("nota", "")]))
    return 1 if resumo["revisar"] or resumo["sem_metadados"] else 0


if __name__ == "__main__":
    sys.exit(main())
