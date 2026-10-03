#!/usr/bin/env python3
"""Verifica preço/disponibilidade dos produtos com 'link' em produtos.json.

Grava uma linha por produto em historico.csv (data, produto, preco, status).
Se o preço mudou desde a última leitura, escreve alertas.md.
Tentativas: JSON-LD (schema.org Product/Offer) -> meta og/product:price.
Sites que bloqueiam robôs ou carregam preço via JS retornam status 'sem_preco'.
"""
import csv
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

AQUI = Path(__file__).parent
UA = "Mozilla/5.0 (compatible; fitness-monitor/1.0)"


def baixar(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", "ignore")


def preco_de(html):
    for bloco in re.findall(r'<script[^>]+ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            dados = json.loads(bloco)
        except ValueError:
            continue
        pilha = dados if isinstance(dados, list) else [dados]
        while pilha:
            x = pilha.pop()
            if isinstance(x, list):
                pilha.extend(x)
            elif isinstance(x, dict):
                if "price" in x or "lowPrice" in x:
                    v = x.get("price", x.get("lowPrice"))
                    try:
                        return float(str(v).replace(",", "."))
                    except ValueError:
                        pass
                pilha.extend(x.values())
    m = re.search(r'(?:product:price:amount|og:price:amount)["\']\s+content=["\']([\d.,]+)', html, re.I)
    if m:
        return float(m.group(1).replace(",", "."))
    return None


def ultimo_preco(csv_path):
    ultimo = {}
    if csv_path.exists():
        for linha in csv.DictReader(csv_path.open(encoding="utf-8")):
            if linha["preco"]:
                ultimo[linha["produto"]] = float(linha["preco"])
    return ultimo


def main():
    produtos = json.loads((AQUI / "produtos.json").read_text(encoding="utf-8"))["produtos"]
    hist = AQUI / "historico.csv"
    antes = ultimo_preco(hist)
    novo = not hist.exists()
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    alertas = []
    with hist.open("a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if novo:
            w.writerow(["data", "produto", "preco", "status", "link"])
        for p in produtos:
            if not p.get("link"):
                continue
            nome = f"{p['nome']} ({p['marca']})"
            try:
                preco = preco_de(baixar(p["link"]))
                status = "ok" if preco is not None else "sem_preco"
            except Exception as e:
                preco, status = None, f"erro:{type(e).__name__}"
            w.writerow([agora, nome, "" if preco is None else preco, status, p["link"]])
            if preco is not None and nome in antes and abs(preco - antes[nome]) > 0.009:
                alertas.append(f"- **{nome}**: R$ {antes[nome]:.2f} → R$ {preco:.2f} ([link]({p['link']}))")
            print(f"{status:<14}{preco if preco is not None else '-':<8}{nome}")
    if alertas:
        (AQUI / "alertas.md").write_text(f"# Mudanças de preço ({agora})\n\n" + "\n".join(alertas) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
