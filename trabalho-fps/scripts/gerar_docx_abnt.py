#!/usr/bin/env python3
"""Gera um artigo científico .docx no padrão ABNT a partir de um JSON.

Normas aplicadas:
  NBR 6022:2018 (estrutura do artigo)   NBR 6023:2018 (referências)
  NBR 6024:2012 (numeração progressiva) NBR 6028:2021 (resumo)
  NBR 10520:2023 (citações)             NBR 14724:2011 (formatação gráfica)
  IBGE (apresentação tabular: tabela aberta x quadro fechado)

Uso:
  python3 gerar_docx_abnt.py trabalhos/<tema>/artigo.json [-o artigo.docx]

Veja modelos/artigo.exemplo.json para o formato de entrada.

Formato "capitulo" (config.formato): capítulo de livro — sem resumo, abstract e palavras-chave;
aceita "capitulo_numero", "epigrafe", "objetivos" (caixa de abertura) e blocos
{"tipo": "caixa", "titulo": "...", "texto": "...", "itens": [...]} para pontos-chave e
aplicações práticas. A ABNT fica só na formatação (margens, fonte, citações, referências).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abnt  # noqa: E402

PADRAO = {
    "fonte": "Arial",            # ou "Times New Roman"
    "tamanho": 12,
    "tamanho_menor": 10,         # citações longas, notas, legendas, fontes
    "estilo_citacao": "2023",    # "2023" (Silva, 2020) | "2002" (SILVA, 2020)
    "autores_referencia": "et_al",  # >3 autores: "et_al" (1º autor + et al.) | "todos"
    "destaque": "negrito",       # destaque do título na referência: negrito | italico
    "formato": "artigo",         # "artigo" (NBR 6022) | "capitulo" (capítulo de livro: sem resumo/abstract)
    "capa": False,               # True = capa institucional (NBR 14724) antes do artigo
    "abstract": True,            # resumo em língua estrangeira
    "apenas_citadas": True,      # lista só as referências citadas no texto
    "cidade": "Recife",
}

ALIGN = {"esquerda": WD_ALIGN_PARAGRAPH.LEFT, "centro": WD_ALIGN_PARAGRAPH.CENTER,
         "direita": WD_ALIGN_PARAGRAPH.RIGHT, "justificado": WD_ALIGN_PARAGRAPH.JUSTIFY}


class ErroEntrada(ValueError):
    pass


# ============================================================ notas de rodapé

class NotasRodape:
    """Notas de rodapé reais do Word (python-docx não oferece nativamente)."""

    def __init__(self, fonte: str, tamanho: int):
        self.notas: list[tuple[int, str]] = []
        self.fonte = fonte
        self.tamanho = tamanho

    def adicionar(self, paragrafo, texto: str) -> None:
        nid = len(self.notas) + 1
        self.notas.append((nid, texto))
        r = OxmlElement("w:r")
        rpr = OxmlElement("w:rPr")
        va = OxmlElement("w:vertAlign")
        va.set(qn("w:val"), "superscript")
        rpr.append(va)
        r.append(rpr)
        ref = OxmlElement("w:footnoteReference")
        ref.set(qn("w:id"), str(nid))
        r.append(ref)
        paragrafo._p.append(r)

    def _xml(self) -> bytes:
        w = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        meia = self.tamanho * 2
        fonte = escape(self.fonte, {'"': "&quot;"})
        rfonts = f'<w:rFonts w:ascii="{fonte}" w:hAnsi="{fonte}" w:cs="{fonte}" w:eastAsia="{fonte}"/>'
        ppr = ('<w:pPr><w:spacing w:before="0" w:after="0" w:line="240" w:lineRule="auto"/>'
               '<w:ind w:firstLine="0"/><w:jc w:val="both"/></w:pPr>')
        partes = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            f'<w:footnotes xmlns:w="{w}">',
            f'<w:footnote w:type="separator" w:id="-1"><w:p>{ppr}<w:r><w:separator/></w:r></w:p></w:footnote>',
            f'<w:footnote w:type="continuationSeparator" w:id="0"><w:p>{ppr}<w:r><w:continuationSeparator/></w:r></w:p></w:footnote>',
        ]
        for nid, texto in self.notas:
            partes.append(
                f'<w:footnote w:id="{nid}"><w:p>{ppr}'
                f'<w:r><w:rPr>{rfonts}<w:sz w:val="{meia}"/><w:szCs w:val="{meia}"/><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteRef/></w:r>'
                f'<w:r><w:rPr>{rfonts}<w:sz w:val="{meia}"/><w:szCs w:val="{meia}"/></w:rPr>'
                f'<w:t xml:space="preserve"> {escape(texto)}</w:t></w:r></w:p></w:footnote>')
        partes.append("</w:footnotes>")
        return "".join(partes).encode("utf-8")

    def gravar(self, doc) -> None:
        if not self.notas:
            return
        part = Part(PackURI("/word/footnotes.xml"),
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.footnotes+xml",
                    self._xml(), doc.part.package)
        doc.part.relate_to(part, RT.FOOTNOTES)
        settings = doc.settings.element
        if settings.find(qn("w:footnotePr")) is None:
            fpr = OxmlElement("w:footnotePr")
            for i in ("-1", "0"):
                f = OxmlElement("w:footnote")
                f.set(qn("w:id"), i)
                fpr.append(f)
            compat = settings.find(qn("w:compat"))
            if compat is not None:
                compat.addprevious(fpr)
            else:
                settings.append(fpr)


# ================================================================ utilidades

def _inserir_antes(pai, el, sucessores: tuple[str, ...]) -> None:
    """Insere 'el' em 'pai' antes do primeiro elemento sucessor (ordem do esquema OOXML)."""
    for filho in pai:
        if filho.tag in {qn(t) for t in sucessores}:
            filho.addprevious(el)
            return
    pai.append(el)


def _set_fonte(rpr_owner, fonte: str) -> None:
    rpr = rpr_owner.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for att in list(rf.attrib):
        if att.endswith("Theme"):
            del rf.attrib[att]
    for att in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(att), fonte)


def _set_idioma(rpr_owner, idioma: str = "pt-BR") -> None:
    rpr = rpr_owner.get_or_add_rPr()
    lang = rpr.find(qn("w:lang"))
    if lang is None:
        lang = OxmlElement("w:lang")
        rpr.append(lang)
    lang.set(qn("w:val"), idioma)


RE_INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*)")


def add_texto(paragrafo, texto: str, *, negrito=False, italico=False, tamanho=None,
              caixa_alta=False) -> None:
    """Adiciona texto com marcação simples: **negrito** e *itálico*."""
    if caixa_alta:
        texto = texto.upper()
    for parte in RE_INLINE.split(texto):
        if not parte:
            continue
        b, i = negrito, italico
        if parte.startswith("**") and parte.endswith("**") and len(parte) > 4:
            parte, b = parte[2:-2], True
        elif parte.startswith("*") and parte.endswith("*") and len(parte) > 2:
            parte, i = parte[1:-1], True
        run = paragrafo.add_run(parte)
        run.bold = b or None
        run.italic = i or None
        if tamanho:
            run.font.size = Pt(tamanho)


def fmt_paragrafo(p, *, alinhamento="justificado", recuo_primeira=None, recuo_esq=None,
                  entrelinha=None, antes=0, depois=0, manter_com_proximo=False):
    pf = p.paragraph_format
    pf.alignment = ALIGN[alinhamento]
    pf.first_line_indent = Cm(recuo_primeira) if recuo_primeira is not None else Cm(0)
    if recuo_esq is not None:
        pf.left_indent = Cm(recuo_esq)
    if entrelinha is not None:
        pf.line_spacing = entrelinha
    pf.space_before = Pt(antes)
    pf.space_after = Pt(depois)
    if manter_com_proximo:
        pf.keep_with_next = True
    return p


def _campo_pagina(paragrafo, tamanho: int) -> None:
    def run_com(el):
        r = paragrafo.add_run()
        r.font.size = Pt(tamanho)
        r._r.append(el)
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); run_com(b)
    it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = " PAGE "; run_com(it)
    s = OxmlElement("w:fldChar"); s.set(qn("w:fldCharType"), "separate"); run_com(s)
    r = paragrafo.add_run("1"); r.font.size = Pt(tamanho)
    e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end"); run_com(e)


def _bordas_tabela(tabela, tipo: str) -> None:
    tbl = tabela._tbl
    tblpr = tbl.tblPr
    for velho in tblpr.findall(qn("w:tblBorders")):
        tblpr.remove(velho)
    borders = OxmlElement("w:tblBorders")

    def borda(nome, val="single", sz="8"):
        el = OxmlElement(f"w:{nome}")
        el.set(qn("w:val"), val)
        el.set(qn("w:sz"), sz)
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "000000")
        borders.append(el)

    if tipo == "quadro":  # quadro: fechado, com todas as linhas
        for n in ("top", "left", "bottom", "right", "insideH", "insideV"):
            borda(n)
    else:  # tabela (IBGE): aberta nas laterais, sem linhas verticais
        borda("top", sz="12"); borda("bottom", sz="12")
        borda("left", "nil"); borda("right", "nil")
        borda("insideH", "nil"); borda("insideV", "nil")
    _inserir_antes(tblpr, borders, ("w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook",
                                    "w:tblCaption", "w:tblDescription"))
    largura = tblpr.find(qn("w:tblW"))
    if largura is None:
        largura = OxmlElement("w:tblW")
        _inserir_antes(tblpr, largura, ("w:jc", "w:tblCellSpacing", "w:tblInd", "w:tblBorders",
                                        "w:shd", "w:tblLayout", "w:tblCellMar", "w:tblLook"))
    largura.set(qn("w:type"), "pct")
    largura.set(qn("w:w"), "5000")


def _borda_celula(celula, lado: str, sz="8") -> None:
    tcpr = celula._tc.get_or_add_tcPr()
    tcb = tcpr.find(qn("w:tcBorders"))
    if tcb is None:
        tcb = OxmlElement("w:tcBorders")
        _inserir_antes(tcpr, tcb, ("w:shd", "w:noWrap", "w:tcMar", "w:textDirection",
                                   "w:tcFitText", "w:vAlign", "w:hideMark"))
    el = OxmlElement(f"w:{lado}")
    el.set(qn("w:val"), "single"); el.set(qn("w:sz"), sz)
    el.set(qn("w:space"), "0"); el.set(qn("w:color"), "000000")
    tcb.append(el)


def _repetir_cabecalho(linha) -> None:
    trpr = linha._tr.get_or_add_trPr()
    h = OxmlElement("w:tblHeader")
    h.set(qn("w:val"), "true")
    trpr.append(h)


# ================================================================== gerador

class GeradorArtigo:
    def __init__(self, dados: dict, base: Path):
        self.d = dados
        self.base = base
        self.cfg = {**PADRAO, **(dados.get("config") or {})}
        self.cfg.setdefault("ano", dt.date.today().year)
        self.refs = self._carregar_refs()
        self.refs = abnt.ordenar_e_desambiguar(self.refs, self.cfg)
        self.cit = abnt.Citador(self.refs, str(self.cfg["estilo_citacao"]))
        self.doc = Document()
        self.notas = NotasRodape(self.cfg["fonte"], self.cfg["tamanho_menor"])
        self.cont = {"tabela": 0, "quadro": 0, "figura": 0}
        self.avisos: list[str] = []

    # ------------------------------------------------------------ entrada
    def _carregar_refs(self) -> list[dict]:
        refs = list(self.d.get("referencias") or [])
        arq = self.d.get("referencias_arquivo")
        if arq:
            refs += abnt.carregar_referencias(self.base / arq)
        ids = [r["id"] for r in refs]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ErroEntrada(f"ids de referência duplicados: {sorted(dup)}")
        return refs

    def t(self, texto: str) -> str:
        return self.cit.aplicar(texto or "")

    # ------------------------------------------------------------ página
    def configurar(self) -> None:
        doc, c = self.doc, self.cfg
        sec = doc.sections[0]
        sec.page_width, sec.page_height = Cm(21), Cm(29.7)
        sec.top_margin, sec.left_margin = Cm(3), Cm(3)
        sec.bottom_margin, sec.right_margin = Cm(2), Cm(2)
        sec.header_distance, sec.footer_distance = Cm(2), Cm(1.25)

        normal = doc.styles["Normal"]
        normal.font.name = c["fonte"]
        normal.font.size = Pt(c["tamanho"])
        normal.font.color.rgb = RGBColor(0, 0, 0)
        _set_fonte(normal.element, c["fonte"])
        _set_idioma(normal.element)
        pf = normal.paragraph_format
        pf.line_spacing = 1.5
        pf.space_before = Pt(0)
        pf.space_after = Pt(0)
        pf.first_line_indent = Cm(1.25)
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.widow_control = True

        # NBR 6024: seções primárias a quinárias diferenciadas tipograficamente.
        niveis = {1: (True, False), 2: (False, False), 3: (True, False),
                  4: (False, True), 5: (False, False)}
        for n, (b, i) in niveis.items():
            st = doc.styles[f"Heading {n}"]
            st.font.name = c["fonte"]
            _set_fonte(st.element, c["fonte"])
            st.font.size = Pt(c["tamanho"])
            st.font.bold = b
            st.font.italic = i
            st.font.all_caps = False
            st.font.color.rgb = RGBColor(0, 0, 0)
            spf = st.paragraph_format
            spf.space_before = Pt(18)
            spf.space_after = Pt(12)
            spf.line_spacing = 1.5
            spf.first_line_indent = Cm(0)
            spf.alignment = WD_ALIGN_PARAGRAPH.LEFT
            spf.keep_with_next = True

        core = doc.core_properties
        core.title = self.d.get("titulo", "")
        core.author = "; ".join(a.get("nome", "") for a in self.d.get("autores", []))
        core.language = "pt-BR"
        core.subject = self.d.get("disciplina", "") or ""

    def cabecalho_paginacao(self, secao) -> None:
        secao.header.is_linked_to_previous = False
        p = secao.header.paragraphs[0]
        fmt_paragrafo(p, alinhamento="direita", entrelinha=1.0)
        _campo_pagina(p, self.cfg["tamanho_menor"])

    # ------------------------------------------------------------ elementos
    def par(self, texto="", **kw):
        p = self.doc.add_paragraph()
        estilo = {k: kw.pop(k) for k in ("negrito", "italico", "tamanho", "caixa_alta") if k in kw}
        kw.setdefault("recuo_primeira", 1.25)
        fmt_paragrafo(p, **kw)
        if texto:
            add_texto(p, self.t(texto), **estilo)
        return p

    def titulo_secao(self, texto: str, nivel: int, numero: str | None, centralizado=False,
                     quebra_pagina=False):
        p = self.doc.add_paragraph(style=f"Heading {min(nivel, 5)}")
        if quebra_pagina:
            p.paragraph_format.page_break_before = True
        if centralizado:
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if nivel <= 2:
            texto = texto.upper()
        rotulo = f"{numero} {texto}" if numero else texto
        add_texto(p, rotulo)
        return p

    def bloco(self, b) -> None:
        if isinstance(b, str):
            b = {"tipo": "paragrafo", "texto": b}
        tipo = b.get("tipo", "paragrafo")
        if tipo == "paragrafo":
            self.par(b["texto"], alinhamento="justificado", entrelinha=1.5)
        elif tipo == "citacao_longa":  # NBR 10520: recuo de 4 cm, fonte menor, espaço simples
            self.par(b["texto"], alinhamento="justificado", recuo_primeira=0, recuo_esq=4,
                     entrelinha=1.0, antes=12, depois=12, tamanho=self.cfg["tamanho_menor"])
        elif tipo == "lista":
            estilo = b.get("estilo", "alineas")
            for i, item in enumerate(b["itens"]):
                marcador = f"{'abcdefghijklmnopqrstuvwxyz'[i % 26]}) " if estilo == "alineas" else "– "
                p = self.par("", alinhamento="justificado", recuo_primeira=-0.6,
                             recuo_esq=1.85, entrelinha=1.5)
                add_texto(p, marcador + self.t(item))
        elif tipo in ("tabela", "quadro"):
            self.tabela(b, tipo)
        elif tipo == "figura":
            self.figura(b)
        elif tipo == "caixa":
            self.caixa(b)
        elif tipo == "quebra_pagina":
            self.doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
        else:
            raise ErroEntrada(f"tipo de bloco desconhecido: {tipo}")

    def legenda(self, rotulo: str, numero: int, titulo: str):
        p = self.par("", alinhamento="esquerda", recuo_primeira=0, entrelinha=1.0, antes=12,
                     depois=3, manter_com_proximo=True)
        add_texto(p, f"{rotulo} {numero} – {self.t(titulo)}", tamanho=self.cfg["tamanho_menor"])
        return p

    def fonte_ilustracao(self, b: dict) -> None:
        if b.get("fonte"):
            p = self.par("", alinhamento="esquerda", recuo_primeira=0, entrelinha=1.0, antes=3)
            add_texto(p, "Fonte: " + self.t(b["fonte"]), tamanho=self.cfg["tamanho_menor"])
        else:
            self.avisos.append(f"ilustração/tabela sem 'fonte': {b.get('titulo')}")
        for nota in ([b["nota"]] if isinstance(b.get("nota"), str) else b.get("nota") or []):
            p = self.par("", alinhamento="justificado", recuo_primeira=0, entrelinha=1.0)
            add_texto(p, "Nota: " + self.t(nota), tamanho=self.cfg["tamanho_menor"])
        self.par("", entrelinha=1.0, depois=6)

    def tabela(self, b: dict, tipo: str) -> None:
        self.cont[tipo] += 1
        self.legenda("Tabela" if tipo == "tabela" else "Quadro", self.cont[tipo], b["titulo"])
        colunas, linhas = b["colunas"], b["linhas"]
        tab = self.doc.add_table(rows=1 + len(linhas), cols=len(colunas))
        tab.alignment = WD_TABLE_ALIGNMENT.CENTER
        tab.autofit = True
        _bordas_tabela(tab, tipo)
        tam = self.cfg["tamanho_menor"]
        for j, nome in enumerate(colunas):
            cel = tab.rows[0].cells[j]
            p = cel.paragraphs[0]
            fmt_paragrafo(p, alinhamento="centro" if tipo == "tabela" else "esquerda",
                          entrelinha=1.0, antes=2, depois=2)
            add_texto(p, self.t(nome), negrito=True, tamanho=tam)
            if tipo == "tabela":
                _borda_celula(cel, "bottom")
        _repetir_cabecalho(tab.rows[0])
        larguras = b.get("larguras_cm")  # opcional, ex.: [3, 2.5, 5, 5.5] (total ≈ 16 cm)
        if larguras and len(larguras) == len(colunas):
            tab.autofit = False
            for j, w in enumerate(larguras):
                tab.columns[j].width = Cm(float(w))  # atualiza tblGrid (LibreOffice/Word respeitam)
                for linha_t in tab.rows:
                    linha_t.cells[j].width = Cm(float(w))
        for i, linha in enumerate(linhas, start=1):
            if len(linha) != len(colunas):
                raise ErroEntrada(f"linha {i} de '{b['titulo']}' tem {len(linha)} células; esperado {len(colunas)}")
            for j, valor in enumerate(linha):
                p = tab.rows[i].cells[j].paragraphs[0]
                numerico = bool(re.fullmatch(r"[\d\s.,%()±–\-<>=;:/IC]+", str(valor)))
                fmt_paragrafo(p, alinhamento="centro" if (numerico and tipo == "tabela") else "esquerda",
                              entrelinha=1.0, antes=2, depois=2)
                add_texto(p, self.t(str(valor)), tamanho=tam)
        self.fonte_ilustracao(b)

    def figura(self, b: dict) -> None:
        self.cont["figura"] += 1
        self.legenda(b.get("rotulo", "Figura"), self.cont["figura"], b["titulo"])
        caminho = (self.base / b["caminho"]).resolve()
        if not caminho.exists():
            raise ErroEntrada(f"imagem não encontrada: {caminho}")
        p = self.doc.add_paragraph()
        fmt_paragrafo(p, alinhamento="centro", entrelinha=1.0)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(caminho), width=Cm(float(b.get("largura_cm", 15))))
        self.fonte_ilustracao(b)

    # ------------------------------------------------------------ partes
    def capa(self) -> None:
        d = self.d
        def linha(txt, antes=0, negrito=False, caixa=True):
            p = self.par("", alinhamento="centro", recuo_primeira=0, entrelinha=1.5, antes=antes)
            add_texto(p, txt, negrito=negrito, caixa_alta=caixa)
        linha(d.get("instituicao", "Faculdade Pernambucana de Saúde"), negrito=True)
        if d.get("curso"):
            linha(d["curso"])
        if d.get("disciplina"):
            linha(d["disciplina"])
        primeiro = True
        for a in d.get("autores", []):
            linha(a["nome"], antes=96 if primeiro else 0)
            primeiro = False
        titulo = d["titulo"].upper() + (f": {d['subtitulo']}" if d.get("subtitulo") else "")
        p = self.par("", alinhamento="centro", recuo_primeira=0, entrelinha=1.5, antes=150)
        add_texto(p, d["titulo"].upper(), negrito=True)
        if d.get("subtitulo"):
            add_texto(p, f": {d['subtitulo']}")
        _ = titulo
        if d.get("orientador"):
            linha(f"Orientador(a): {d['orientador']['nome']}", antes=48, caixa=False)
        linha(self.cfg["cidade"], antes=170)
        linha(str(self.cfg["ano"]))
        nova = self.doc.add_section(WD_SECTION.NEW_PAGE)
        pg = OxmlElement("w:pgNumType")
        pg.set(qn("w:start"), "1")
        _inserir_antes(nova._sectPr, pg, ("w:cols", "w:formProt", "w:vAlign", "w:noEndnote",
                                          "w:titlePg", "w:textDirection", "w:bidi", "w:rtlGutter",
                                          "w:docGrid", "w:printerSettings", "w:sectPrChange"))

    def abertura(self) -> None:
        d = self.d
        if self.cfg.get("formato") == "capitulo" and d.get("capitulo_numero") is not None:
            self.par(f"CAPÍTULO {d['capitulo_numero']}", alinhamento="centro", recuo_primeira=0,
                     entrelinha=1.5, depois=6)
        p = self.par("", alinhamento="centro", recuo_primeira=0, entrelinha=1.5)
        add_texto(p, d["titulo"].upper(), negrito=True)
        if d.get("subtitulo"):
            add_texto(p, f": {d['subtitulo']}")
        if d.get("titulo_en"):
            p = self.par("", alinhamento="centro", recuo_primeira=0, entrelinha=1.5, antes=6)
            add_texto(p, d["titulo_en"], italico=True)
        primeiro = True
        for a in d.get("autores", []):
            p = self.par("", alinhamento="direita", recuo_primeira=0, entrelinha=1.0,
                         antes=24 if primeiro else 0)
            primeiro = False
            add_texto(p, a["nome"])
            if a.get("nota"):
                self.notas.adicionar(p, a["nota"])
        if d.get("orientador"):
            o = d["orientador"]
            p = self.par("", alinhamento="direita", recuo_primeira=0, entrelinha=1.0)
            add_texto(p, o["nome"])
            if o.get("nota"):
                self.notas.adicionar(p, o["nota"])

    def caixa(self, b: dict) -> None:
        """Caixa de destaque (pontos-chave, na prática, objetivos): tabela de 1 célula sombreada."""
        self.par("", entrelinha=1.0, depois=2)
        tab = self.doc.add_table(rows=1, cols=1)
        tab.alignment = WD_TABLE_ALIGNMENT.CENTER
        _bordas_tabela(tab, "quadro")
        trpr = tab.rows[0]._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))  # caixa não quebra entre páginas
        cel = tab.rows[0].cells[0]
        tcpr = cel._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), b.get("cor", "F2F2F2"))
        _inserir_antes(tcpr, shd, ("w:noWrap", "w:tcMar", "w:textDirection", "w:tcFitText", "w:vAlign", "w:hideMark"))
        p = cel.paragraphs[0]
        fmt_paragrafo(p, alinhamento="esquerda", entrelinha=1.15, antes=4, depois=4)
        add_texto(p, self.t(b.get("titulo", "")), negrito=True)
        if b.get("texto"):
            q = cel.add_paragraph()
            fmt_paragrafo(q, alinhamento="justificado", entrelinha=1.15, depois=4)
            add_texto(q, self.t(b["texto"]), tamanho=self.cfg["tamanho"] - 1)
        for item in b.get("itens", []):
            q = cel.add_paragraph()
            fmt_paragrafo(q, alinhamento="justificado", recuo_primeira=-0.5, recuo_esq=0.7, entrelinha=1.15, depois=3)
            add_texto(q, "• " + self.t(item), tamanho=self.cfg["tamanho"] - 1)
        self.par("", entrelinha=1.0, depois=6)

    def abertura_capitulo(self) -> None:
        d = self.d
        if d.get("epigrafe"):
            self.par(d["epigrafe"], alinhamento="direita", recuo_primeira=0, recuo_esq=8, entrelinha=1.0,
                     antes=18, depois=12, italico=True, tamanho=self.cfg["tamanho_menor"])
        if d.get("objetivos"):
            self.par("", entrelinha=1.0, depois=6)
            self.caixa({"titulo": d.get("objetivos_titulo", "Ao final deste capítulo, você será capaz de:"),
                        "itens": d["objetivos"]})

    def resumo(self, rotulo: str, texto: str, rot_pc: str, palavras: list[str]) -> None:
        self.titulo_secao(rotulo, 1, None, centralizado=True)
        self.par(texto, alinhamento="justificado", recuo_primeira=0, entrelinha=1.0)
        p = self.par("", alinhamento="justificado", recuo_primeira=0, entrelinha=1.0, antes=12)
        add_texto(p, f"{rot_pc}: ", negrito=True)
        add_texto(p, "; ".join(x.strip().rstrip(".") for x in palavras) + ".")

    def secoes(self, lista: list[dict], prefixo: str = "", nivel: int = 1) -> None:
        n = 0
        for s in lista:
            numerada = s.get("numerada", True)
            numero = None
            if numerada:
                n += 1
                numero = f"{prefixo}{n}"
            self.titulo_secao(s["titulo"], nivel, numero)
            for b in s.get("blocos", []):
                self.bloco(b)
            if s.get("subsecoes"):
                self.secoes(s["subsecoes"], f"{numero}." if numero else prefixo, nivel + 1)

    def referencias(self) -> None:
        citadas = set(self.cit.citadas)
        lista = [r for r in self.refs if r["id"] in citadas] if self.cfg["apenas_citadas"] else self.refs
        nao_citadas = [r["id"] for r in self.refs if r["id"] not in citadas]
        if nao_citadas:
            self.avisos.append(
                f"{len(nao_citadas)} referência(s) não citada(s) no texto"
                f"{' (omitidas da lista)' if self.cfg['apenas_citadas'] else ''}: {', '.join(nao_citadas)}")
        self.titulo_secao("Referências", 1, None, centralizado=True)
        for r in lista:
            p = self.par("", alinhamento="esquerda", recuo_primeira=0, entrelinha=1.0, depois=12)
            for txt, est in abnt.referencia_segmentos(r, self.cfg):
                run = p.add_run(txt)
                run.bold = True if est == "b" else None
                run.italic = True if est == "i" else None
        self.n_refs = len(lista)

    def pos_textuais(self, chave: str, rotulo: str) -> None:
        for i, ap in enumerate(self.d.get(chave) or []):
            letra = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i]
            self.titulo_secao(f"{rotulo} {letra} – {ap['titulo']}", 1, None, centralizado=True,
                              quebra_pagina=True)
            for b in ap.get("blocos", []):
                self.bloco(b)

    # ------------------------------------------------------------ fluxo
    def gerar(self, saida: Path) -> dict:
        d = self.d
        capitulo = self.cfg.get("formato") == "capitulo"
        obrig = ("titulo", "autores", "secoes") if capitulo else ("titulo", "autores", "resumo", "palavras_chave", "secoes")
        for campo in obrig:
            if not d.get(campo):
                raise ErroEntrada(f"campo obrigatório ausente: '{campo}'")
        self.configurar()
        if self.cfg["capa"]:
            self.capa()
        self.cabecalho_paginacao(self.doc.sections[-1])
        if self.cfg["capa"]:
            # A capa não exibe número de página.
            self.doc.sections[0].header.is_linked_to_previous = False
        self.abertura()
        if capitulo:
            self.abertura_capitulo()
        else:
            self.resumo("Resumo", d["resumo"], "Palavras-chave", d["palavras_chave"])
        if not capitulo and self.cfg["abstract"] and d.get("abstract"):
            self.resumo("Abstract", d["abstract"], "Keywords", d.get("keywords") or [])
        self.secoes(d["secoes"])
        self.referencias()
        self.pos_textuais("apendices", "APÊNDICE")
        self.pos_textuais("anexos", "ANEXO")
        if d.get("agradecimentos"):
            self.titulo_secao("Agradecimentos", 1, None, centralizado=True)
            self.par(d["agradecimentos"])
        self.notas.gravar(self.doc)
        saida.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(saida))
        palavras = sum(len(re.findall(r"\w+", p.text)) for p in self.doc.paragraphs)
        return {
            "arquivo": str(saida), "palavras": palavras,
            "referencias_listadas": self.n_refs, "citadas": len(self.cit.citadas),
            "ids_inexistentes": self.cit.ausentes, "tabelas": self.cont["tabela"],
            "quadros": self.cont["quadro"], "figuras": self.cont["figura"], "avisos": self.avisos,
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json", type=Path)
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--permitir-pendencias", action="store_true",
                    help="gera mesmo com citações para ids inexistentes (marcadas ??id??)")
    a = ap.parse_args()
    dados = json.loads(a.json.read_text(encoding="utf-8"))
    saida = a.saida or a.json.with_suffix(".docx")
    try:
        res = GeradorArtigo(dados, a.json.parent).gerar(saida)
    except (ErroEntrada, abnt.ErroReferencia, KeyError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if res["ids_inexistentes"] and not a.permitir_pendencias:
        print(f"ERRO: citações sem referência correspondente: {res['ids_inexistentes']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
