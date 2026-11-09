#!/usr/bin/env python3
"""Validador final do trabalho (artigo + referências + slides).

Uso:
  python3 validar_trabalho.py trabalhos/<pasta-do-tema> [--tolerante] [--final]

Verifica, entre outros pontos:
  - integridade das citações (todo [@id] existe; toda referência é citada);
  - referências verificadas (campo "verificado": true) e rastreáveis (DOI/PMID/URL);
  - resumo com 100–250 palavras e 3–5 palavras-chave (NBR 6028:2021);
  - estrutura mínima (Introdução ... Considerações finais/Conclusão);
  - redundância (parágrafos/slides quase idênticos);
  - slides: ≤ 5 tópicos, tópicos curtos, notas do apresentador, fonte nos slides de dados;
  - governança: último parecer de cada etapa aprovado no portão (--final exige todas + banca.md).
Gera <pasta>/validacao.md. Código de saída 1 se houver ERROS.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abnt  # noqa: E402

LAYOUTS_COM_FONTE = {"numeros", "tabela", "evidencias", "fluxo", "picos"}


def palavras(txt: str) -> int:
    txt = re.sub(r"\[@[^\]]+\]|\*\*|\*", "", txt or "")
    return len(re.findall(r"\w+", txt))


def textos_blocos(blocos) -> list[str]:
    out = []
    for b in blocos or []:
        if isinstance(b, str):
            out.append(b)
        elif b.get("tipo") in ("paragrafo", "citacao_longa"):
            out.append(b.get("texto", ""))
        elif b.get("tipo") == "lista":
            out += b.get("itens", [])
        elif b.get("tipo") in ("tabela", "quadro"):
            out.append(b.get("titulo", ""))
            out.append(b.get("fonte", ""))
            out += [" ".join(map(str, linha)) for linha in b.get("linhas", [])]
        elif b.get("tipo") == "figura":
            out += [b.get("titulo", ""), b.get("fonte", "")]
    return out


def percorrer_secoes(secoes, caminho=""):
    for s in secoes or []:
        nome = f"{caminho} > {s['titulo']}" if caminho else s["titulo"]
        yield nome, s
        yield from percorrer_secoes(s.get("subsecoes"), nome)


class Relatorio:
    def __init__(self):
        self.erros, self.avisos, self.info = [], [], []

    def erro(self, m):
        self.erros.append(m)

    def aviso(self, m):
        self.avisos.append(m)

    def nota(self, m):
        self.info.append(m)

    def markdown(self, pasta: Path) -> str:
        linhas = [f"# Validação — {pasta.name}", "",
                  f"Gerado em {dt.datetime.now():%d/%m/%Y %H:%M}.", "",
                  f"**Resultado:** {'❌ REPROVADO' if self.erros else '✅ APROVADO'} "
                  f"({len(self.erros)} erro(s), {len(self.avisos)} aviso(s))", ""]
        for titulo, lista in (("Erros (corrigir antes de entregar)", self.erros),
                              ("Avisos (revisar)", self.avisos), ("Indicadores", self.info)):
            linhas.append(f"## {titulo}")
            linhas += [f"- {x}" for x in lista] or ["- nenhum"]
            linhas.append("")
        return "\n".join(linhas)


def validar_referencias(refs: list[dict], rel: Relatorio, tolerante: bool):
    ano_atual = dt.date.today().year
    for r in refs:
        rid = r.get("id")
        try:
            abnt.referencia_texto(r)
        except abnt.ErroReferencia as e:
            rel.erro(f"referência mal formada: {e}")
        if not r.get("verificado"):
            (rel.aviso if tolerante else rel.erro)(
                f"[{rid}] não verificada (\"verificado\": true ausente) — confirmar existência no PubMed/DOI")
        if not (r.get("doi") or r.get("pmid") or r.get("url")):
            if r.get("tipo") in ("livro", "capitulo"):
                rel.nota(f"[{rid}] livro sem DOI/URL (aceitável; confira edição e editora)")
            else:
                rel.aviso(f"[{rid}] sem DOI, PMID ou URL — rastreabilidade comprometida")
        if not r.get("ano"):
            rel.erro(f"[{rid}] sem ano")
        if not (r.get("autores") or r.get("autor_entidade")):
            rel.aviso(f"[{rid}] sem autoria (entrada pelo título)")
    anos = [int(r["ano"]) for r in refs if str(r.get("ano", "")).isdigit()]
    if anos:
        recentes = sum(1 for a in anos if a >= ano_atual - 5)
        rel.nota(f"{len(refs)} referência(s); {recentes} ({100 * recentes // len(anos)}%) dos últimos 5 anos; "
                 f"mais antiga: {min(anos)}")
    desenhos = Counter((r.get("desenho") or "não informado") for r in refs)
    rel.nota("desenhos: " + "; ".join(f"{k}: {v}" for k, v in desenhos.most_common()))


def validar_artigo(art: dict, refs: list[dict], rel: Relatorio) -> set[str]:
    for campo in ("titulo", "autores", "resumo", "palavras_chave", "secoes"):
        if not art.get(campo):
            rel.erro(f"artigo sem campo obrigatório '{campo}'")
    n = palavras(art.get("resumo", ""))
    if not 100 <= n <= 250:
        rel.erro(f"resumo com {n} palavras (NBR 6028: artigos 100–250)")
    else:
        rel.nota(f"resumo: {n} palavras")
    pc = art.get("palavras_chave") or []
    if not 3 <= len(pc) <= 5:
        rel.aviso(f"{len(pc)} palavras-chave (recomendado 3–5, preferir descritores DeCS)")
    if (art.get("config") or {}).get("abstract", True) and not art.get("abstract"):
        rel.aviso("abstract ausente (resumo em língua estrangeira)")
    if art.get("abstract") and art.get("keywords") and len(art["keywords"]) != len(pc):
        rel.aviso("número de keywords diferente do de palavras-chave")
    titulos = [s["titulo"].lower() for s in art.get("secoes", [])]
    if titulos and "introdu" not in titulos[0]:
        rel.aviso("primeira seção não é 'Introdução'")
    if titulos and not any(k in titulos[-1] for k in ("considera", "conclus")):
        rel.aviso("última seção não é 'Considerações finais' ou 'Conclusão'")

    textos = [art.get("resumo", "")]
    citados: list[str] = []
    total = 0
    for nome, s in percorrer_secoes(art.get("secoes")):
        ts = textos_blocos(s.get("blocos"))
        textos += ts
        ids = [i for t in ts for i in abnt.ids_citados(t)]
        citados += ids
        total += sum(palavras(t) for t in ts)
        if any(k in nome.lower() for k in ("considera", "conclus")) and ids:
            rel.aviso(f"seção '{nome}' contém citações — considerações finais não devem trazer evidência nova")
    rel.nota(f"corpo do texto: ~{total} palavras")

    validos = set()
    for r in refs:
        validos.add(r["id"])
        validos.update(r.get("aliases") or [])
    ausentes = sorted(set(citados) - validos)
    for a in ausentes:
        rel.erro(f"citação [@{a}] sem referência correspondente")
    usados = set()
    por_alias = {a: r["id"] for r in refs for a in (r.get("aliases") or [])}
    for c in citados:
        usados.add(por_alias.get(c, c))
    nao_citadas = [r["id"] for r in refs if r["id"] not in usados]
    if nao_citadas:
        rel.aviso(f"{len(nao_citadas)} referência(s) não citada(s) no artigo (serão omitidas da lista): "
                  + ", ".join(nao_citadas))
    if any("??" in t for t in textos):
        rel.erro("texto contém marcadores '??' (pendências)")

    paragrafos = [re.sub(r"\W+", " ", t.lower()) for t in textos if palavras(t) > 25]
    for i in range(len(paragrafos)):
        for j in range(i + 1, len(paragrafos)):
            if difflib.SequenceMatcher(None, paragrafos[i], paragrafos[j]).ratio() > 0.8:
                rel.aviso(f"parágrafos muito parecidos (redundância): \"{paragrafos[i][:70]}...\"")
    return usados


def validar_slides(sl: dict, refs: list[dict], rel: Relatorio):
    slides = sl.get("slides", [])
    rel.nota(f"{len(slides)} slide(s) definidos")
    tempo = sl.get("tempo_minutos")
    if tempo:
        if len(slides) > tempo * 1.3 + 3:
            rel.aviso(f"{len(slides)} slides para {tempo} min — risco de estourar o tempo (≈1 slide/min)")
        elif len(slides) < tempo * 0.5:
            rel.aviso(f"apenas {len(slides)} slides para {tempo} min")
    validos = {r["id"] for r in refs} | {a for r in refs for a in (r.get("aliases") or [])}
    vistos: list[tuple[int, str]] = []
    for k, s in enumerate(slides, start=1):
        lay = s.get("layout", "topicos")
        strings = []

        def coletar(v):
            if isinstance(v, str):
                strings.append(v)
            elif isinstance(v, list):
                for x in v:
                    coletar(x)
            elif isinstance(v, dict):
                for x in v.values():
                    coletar(x)
        coletar({kk: vv for kk, vv in s.items() if kk != "notas"})
        for st in strings:
            for i in abnt.ids_citados(st):
                if i not in validos:
                    rel.erro(f"slide {k}: citação [@{i}] sem referência")
        itens = s.get("itens", [])
        if lay in ("topicos", "conclusao") and len(itens) > 5:
            rel.aviso(f"slide {k}: {len(itens)} tópicos (máx. 5)")
        for it in itens:
            txt = it.get("texto", "") if isinstance(it, dict) else str(it)
            if palavras(txt) > 14:
                rel.aviso(f"slide {k}: tópico longo ({palavras(txt)} palavras) → mover detalhe para as notas")
        if lay in LAYOUTS_COM_FONTE and not s.get("fonte"):
            rel.aviso(f"slide {k} ({lay}): sem 'fonte' no rodapé")
        if lay not in ("capa", "secao", "encerramento", "referencias") and not s.get("notas"):
            rel.aviso(f"slide {k}: sem notas do apresentador")
        for st in [s.get("titulo", "")] + [i if isinstance(i, str) else i.get("texto", "") for i in itens]:
            limpo = re.sub(r"\W+", " ", st.lower()).strip()
            if len(limpo) < 18:
                continue
            for k0, ant in vistos:
                if difflib.SequenceMatcher(None, limpo, ant).ratio() > 0.82:
                    rel.aviso(f"slide {k}: repete conteúdo do slide {k0} → \"{st[:60]}\"")
                    break
            vistos.append((k, limpo))


def validar_governanca(pasta: Path, rel: Relatorio, final: bool):
    """Confere o ciclo de revisão hierárquica (pareceres + portões)."""
    import parecer as pc
    if not (pasta / "revisoes").is_dir():
        (rel.erro if final else rel.aviso)("sem pasta revisoes/ — o trabalho não passou pela revisão hierárquica")
        return
    todos = pc.pareceres(pasta)
    resumo = []
    for etapa in pc.ORDEM_ETAPAS:
        if etapa not in todos:
            (rel.erro if final else rel.aviso)(f"etapa '{etapa}' sem parecer de revisão")
            continue
        rodada, arq = todos[etapa][-1]
        try:
            par = json.loads(arq.read_text(encoding="utf-8"))
            decisao, _, est = pc.avaliar(par)
        except (pc.ParecerInvalido, json.JSONDecodeError) as e:
            rel.erro(f"parecer inválido em {arq.name}: {e}")
            continue
        resumo.append(f"{etapa}: {decisao} (r{rodada}, média {est['media']:.1f})")
        if decisao != "APROVADO":
            (rel.erro if final else rel.aviso)(f"etapa '{etapa}' não aprovada no portão ({decisao}, rodada {rodada})")
    if resumo:
        rel.nota("portões: " + " · ".join(resumo))
    if final and not (pasta / "banca.md").exists():
        rel.erro("banca.md ausente — a auditoria final (fps-banca) não rodou")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pasta", type=Path)
    ap.add_argument("--tolerante", action="store_true", help="referência não verificada vira aviso")
    ap.add_argument("--final", action="store_true",
                    help="entrega final: exige todas as etapas aprovadas no portão e banca.md")
    a = ap.parse_args()
    pasta = a.pasta
    rel = Relatorio()

    for arq in ("00-briefing.md", "01-investigacao.md", "02-analise-critica.md", "03-evidencias.md"):
        if not (pasta / arq).exists():
            rel.aviso(f"etapa ausente: {arq}")

    refs: list[dict] = []
    art = None
    if (pasta / "artigo.json").exists():
        art = json.loads((pasta / "artigo.json").read_text(encoding="utf-8"))
        refs = list(art.get("referencias") or [])
        if art.get("referencias_arquivo"):
            refs += abnt.carregar_referencias(pasta / art["referencias_arquivo"])
    elif (pasta / "referencias.json").exists():
        refs = abnt.carregar_referencias(pasta / "referencias.json")

    if art is not None:
        usados = validar_artigo(art, refs, rel)
        validar_referencias([r for r in refs if r["id"] in usados] or refs, rel, a.tolerante)
        if not (pasta / "artigo.docx").exists():
            rel.aviso("artigo.docx ainda não gerado")
    else:
        rel.aviso("artigo.json não encontrado")

    if (pasta / "slides.json").exists():
        sl = json.loads((pasta / "slides.json").read_text(encoding="utf-8"))
        refs_sl = refs
        if sl.get("referencias_arquivo") and not refs:
            refs_sl = abnt.carregar_referencias(pasta / sl["referencias_arquivo"])
        validar_slides(sl, refs_sl, rel)
        if not (pasta / "apresentacao.pptx").exists():
            rel.aviso("apresentacao.pptx ainda não gerada")

    validar_governanca(pasta, rel, a.final)

    md = rel.markdown(pasta)
    if pasta.is_dir():
        (pasta / "validacao.md").write_text(md, encoding="utf-8")
    print(md)
    return 1 if rel.erros else 0


if __name__ == "__main__":
    sys.exit(main())
