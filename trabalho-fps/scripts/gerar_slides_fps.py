#!/usr/bin/env python3
"""Gera apresentação .pptx (16:9) com a identidade visual da FPS a partir de um JSON.

Uso:
  python3 gerar_slides_fps.py trabalhos/<tema>/slides.json [-o apresentacao.pptx]

Layouts disponíveis (campo "layout" de cada slide):
  capa, secao, topicos, dois_colunas, fluxo, numeros, tabela, picos,
  evidencias, mensagem, conclusao, imagem, referencias, encerramento

Princípios embutidos (apresentação limpa, direta e sem redundância):
  - uma ideia por slide; título = mensagem (frase-afirmação), não rótulo;
  - no máximo 5 tópicos curtos; o detalhe vai para as notas do apresentador;
  - toda informação baseada em estudo leva "fonte" no rodapé (autor-data ABNT);
  - o gerador emite AVISOS de texto excessivo e de conteúdo repetido.

Veja modelos/slides.exemplo.json para o formato de entrada.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import abnt  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
W, H = 13.333, 7.5
MX = 0.7                 # margem lateral
TOPO_CONTEUDO = 1.95
BASE_CONTEUDO = 6.65

MARCA_PADRAO = {
    "instituicao": "Faculdade Pernambucana de Saúde",
    "sigla": "FPS",
    "logo": "logo-fps.png",
    "logo_negativo": "logo-fps-branco.png",
    "cores": {
        "primaria": "#0B3B60", "secundaria": "#0F8B8D", "destaque": "#F2A900",
        "texto": "#1E293B", "texto_suave": "#64748B", "fundo": "#FFFFFF",
        "fundo_suave": "#F1F5F9", "texto_sobre_primaria": "#FFFFFF",
        "texto_sobre_primaria_suave": "#C9D8E6",
    },
    "fontes": {"titulos": "Calibri", "corpo": "Calibri"},
}

LIMITES = {"topicos": 5, "palavras_por_topico": 14, "caracteres_titulo": 90}


def altura_texto(texto: str, largura_pol: float, tamanho_pt: float, entre: float = 1.2) -> float:
    """Estimativa (polegadas) da altura ocupada por um texto quebrado em linhas."""
    import math
    limpo = re.sub(r"\*\*|\[@[^\]]+\]", "", str(texto or ""))
    por_linha = max(1, int(largura_pol * 144 / tamanho_pt))
    linhas = sum(max(1, math.ceil(len(par) / por_linha)) for par in limpo.split("\n"))
    return linhas * tamanho_pt * entre / 72


def rgb(hexa: str) -> RGBColor:
    return RGBColor.from_string(hexa.lstrip("#").upper())


class ErroEntrada(ValueError):
    pass


# ============================================================ marca

class Marca:
    def __init__(self, caminho: Path | None, sobrescrever: dict | None = None):
        dados = json.loads(json.dumps(MARCA_PADRAO))
        self.pasta = RAIZ / "marca"
        if caminho and caminho.exists():
            lido = json.loads(caminho.read_text(encoding="utf-8"))
            self.pasta = caminho.parent
            for k, v in lido.items():
                if isinstance(v, dict) and isinstance(dados.get(k), dict):
                    dados[k].update(v)
                else:
                    dados[k] = v
        for k, v in (sobrescrever or {}).items():
            if isinstance(v, dict) and isinstance(dados.get(k), dict):
                dados[k].update(v)
            else:
                dados[k] = v
        self.d = dados
        self.c = {k: rgb(v) for k, v in dados["cores"].items()}
        self.hex = dados["cores"]
        self.fonte_titulo = dados["fontes"]["titulos"]
        self.fonte_corpo = dados["fontes"]["corpo"]

    def arquivo(self, chave: str) -> Path | None:
        nome = self.d.get(chave)
        if not nome:
            return None
        p = (self.pasta / nome)
        return p if p.exists() else None


# ============================================================ primitivas

def _sem_estilo(shape) -> None:
    """Remove o estilo de tema (evita sombras/contornos herdados)."""
    st = shape._element.find(qn("p:style"))
    if st is not None:
        shape._element.remove(st)


def _alpha(shape, opacidade: float) -> None:
    srgb = shape.fill._xPr.find(qn("a:solidFill")).find(qn("a:srgbClr"))
    a = srgb.makeelement(qn("a:alpha"), {"val": str(int(opacidade * 100000))})
    srgb.append(a)


class Construtor:
    def __init__(self, dados: dict, base: Path, marca: Marca, refs: list[dict]):
        self.d = dados
        self.base = base
        self.m = marca
        self.prs = Presentation()
        self.prs.slide_width = Inches(W)
        self.prs.slide_height = Inches(H)
        self.layout_vazio = self.prs.slide_layouts[6]
        self.refs = abnt.ordenar_e_desambiguar(refs, {}) if refs else []
        self.cit = abnt.Citador(self.refs, str(dados.get("estilo_citacao", "2023")))
        self.avisos: list[str] = []
        self.textos_vistos: list[tuple[int, str]] = []
        self.n = 0

    # ---------------------------------------------------------------- texto
    def t(self, s) -> str:
        return self.cit.aplicar(str(s)) if s else ""

    def forma(self, slide, x, y, w, h, cor=None, tipo=MSO_SHAPE.RECTANGLE, raio=None,
              opacidade=None, contorno=None):
        sh = slide.shapes.add_shape(tipo, Inches(x), Inches(y), Inches(w), Inches(h))
        _sem_estilo(sh)
        if cor is None:
            sh.fill.background()
        else:
            sh.fill.solid()
            sh.fill.fore_color.rgb = cor
            if opacidade is not None:
                _alpha(sh, opacidade)
        if contorno:
            sh.line.color.rgb = contorno
            sh.line.width = Pt(1)
        else:
            sh.line.fill.background()
        if raio is not None and tipo == MSO_SHAPE.ROUNDED_RECTANGLE:
            sh.adjustments[0] = raio
        return sh

    def texto(self, slide, x, y, w, h, conteudo, tamanho=18, cor=None, negrito=False,
              italico=False, alinhar="esq", ancora="topo", fonte=None, entre=None,
              realce=None, espaco_depois=0):
        """conteudo: str ou lista de str (um parágrafo por item).
        **trecho** fica em negrito (e na cor 'realce', se informada)."""
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = Emu(0)
        tf.margin_top = tf.margin_bottom = Emu(0)
        tf.vertical_anchor = {"topo": MSO_ANCHOR.TOP, "meio": MSO_ANCHOR.MIDDLE,
                              "base": MSO_ANCHOR.BOTTOM}[ancora]
        paragrafos = conteudo if isinstance(conteudo, list) else [conteudo]
        for i, par in enumerate(paragrafos):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"esq": PP_ALIGN.LEFT, "centro": PP_ALIGN.CENTER,
                           "dir": PP_ALIGN.RIGHT}[alinhar]
            if entre:
                p.line_spacing = entre
            if espaco_depois:
                p.space_after = Pt(espaco_depois)
            self._runs(p, self.t(par), tamanho, cor, negrito, italico, fonte, realce)
        return tb

    def _runs(self, p, s, tamanho, cor, negrito, italico, fonte, realce=None):
        for parte in re.split(r"(\*\*.+?\*\*)", s):
            if not parte:
                continue
            forte = parte.startswith("**") and parte.endswith("**") and len(parte) > 4
            r = p.add_run()
            r.text = parte[2:-2] if forte else parte
            f = r.font
            f.size = Pt(tamanho)
            f.bold = negrito or forte
            f.italic = italico
            f.name = fonte or self.m.fonte_corpo
            c = realce if (forte and realce is not None) else cor
            f.color.rgb = c if c is not None else self.m.c["texto"]

    def topicos_em(self, slide, x, y, w, h, itens, tamanho, cor=None):
        tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
        primeiro = True
        for item in itens:
            subs = []
            if isinstance(item, dict):
                subs = item.get("sub", [])
                item = item.get("texto", "")
            for nivel, txt in [(0, item)] + [(1, s) for s in subs]:
                p = tf.paragraphs[0] if primeiro else tf.add_paragraph()
                primeiro = False
                self._marcador(p, nivel, tamanho)
                p.space_after = Pt(tamanho * (0.75 if nivel == 0 else 0.4))
                p.line_spacing = 1.05
                self._runs(p, self.t(txt), tamanho if nivel == 0 else tamanho - 3,
                           cor if nivel == 0 else self.m.c["texto_suave"], False, False, None,
                           self.m.c["primaria"])
        return tb

    def _marcador(self, p, nivel, tamanho):
        pPr = p._p.get_or_add_pPr()
        recuo = int(Inches(0.38 if nivel == 0 else 0.3))
        pPr.set("marL", str(recuo + (int(Inches(0.38)) if nivel else 0)))
        pPr.set("indent", str(-recuo))
        for tag in ("a:buNone", "a:buChar", "a:buClr", "a:buSzPct", "a:buFont"):
            for el in pPr.findall(qn(tag)):
                pPr.remove(el)
        buClr = pPr.makeelement(qn("a:buClr"), {})
        cor = self.m.hex["secundaria"] if nivel == 0 else self.m.hex["texto_suave"]
        buClr.append(buClr.makeelement(qn("a:srgbClr"), {"val": cor.lstrip("#").upper()}))
        pPr.append(buClr)
        pPr.append(pPr.makeelement(qn("a:buSzPct"), {"val": "80000" if nivel == 0 else "70000"}))
        pPr.append(pPr.makeelement(qn("a:buFont"), {"typeface": "Arial"}))
        pPr.append(pPr.makeelement(qn("a:buChar"), {"char": "■" if nivel == 0 else "–"}))

    # ---------------------------------------------------------------- moldura
    def novo(self, fundo=None):
        s = self.prs.slides.add_slide(self.layout_vazio)
        self.n += 1
        if fundo is not None:
            self.forma(s, 0, 0, W, H, fundo)
        return s

    def logo(self, slide, x_dir, y, h, escuro=False):
        caminho = self.m.arquivo("logo_negativo") if escuro else None
        usa_pilula = False
        if caminho is None:
            caminho = self.m.arquivo("logo")
            usa_pilula = escuro and caminho is not None
        if caminho is None:
            # Sem arquivo de logo: marcador textual (avisado no relatório).
            cor = self.m.c["texto_sobre_primaria"] if escuro else self.m.c["primaria"]
            self.texto(slide, x_dir - 3.2, y, 3.2, h, f"**{self.m.d['sigla']}**  {self.m.d['instituicao']}",
                       tamanho=11, cor=cor, alinhar="dir", ancora="meio",
                       realce=cor)
            return
        from PIL import Image
        with Image.open(caminho) as im:
            proporcao = im.width / im.height
        w = h * proporcao
        x = x_dir - w
        if usa_pilula:
            pad = h * 0.25
            self.forma(slide, x - pad, y - pad, w + 2 * pad, h + 2 * pad, self.m.c["fundo"],
                       MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.25)
        slide.shapes.add_picture(str(caminho), Inches(x), Inches(y), Inches(w), Inches(h))

    def titulo(self, slide, txt):
        txt = self.t(txt)
        n = len(txt)
        if n > LIMITES["caracteres_titulo"]:
            self.avisos.append(f"slide {self.n}: título longo ({n} caracteres) — reduza para uma frase direta")
        tam = 30 if n <= 55 else 26 if n <= 85 else 22
        self.texto(slide, MX, 0.42, W - 2 * MX, 1.05, txt, tamanho=tam, cor=self.m.c["primaria"],
                   negrito=True, ancora="base", fonte=self.m.fonte_titulo, entre=0.95)
        self.forma(slide, MX, 1.6, 0.9, 0.07, self.m.c["secundaria"])
        self._registrar(txt)

    def rodape(self, slide, fonte=None):
        self.texto(slide, MX, 6.98, 0.6, 0.3, f"{self.n:02d}", tamanho=11, cor=self.m.c["secundaria"],
                   negrito=True, ancora="meio")
        if fonte:
            txt = self.t(fonte).strip()
            if txt.startswith("(") and txt.endswith(")") and txt.count("(") == 1:
                txt = txt[1:-1]
            self.texto(slide, MX + 0.6, 6.98, 9.6, 0.3, f"Fonte: {txt}", tamanho=10,
                       cor=self.m.c["texto_suave"], ancora="meio")
        self.logo(slide, W - MX, 6.86, 0.4)

    def notas(self, slide, s: dict):
        if s.get("notas"):
            slide.notes_slide.notes_text_frame.text = self.t(s["notas"])
        elif s.get("layout") not in ("capa", "secao", "encerramento", "referencias"):
            self.avisos.append(f"slide {self.n}: sem 'notas' do apresentador")

    def _registrar(self, txt: str):
        limpo = re.sub(r"\W+", " ", txt.lower()).strip()
        if len(limpo) < 18:
            return
        for n_ant, ant in self.textos_vistos:
            if difflib.SequenceMatcher(None, limpo, ant).ratio() > 0.82:
                self.avisos.append(f"slide {self.n}: conteúdo repetido do slide {n_ant} → \"{txt[:60]}\"")
                break
        self.textos_vistos.append((self.n, limpo))

    def _checar_topicos(self, itens):
        if len(itens) > LIMITES["topicos"]:
            self.avisos.append(f"slide {self.n}: {len(itens)} tópicos (máx. {LIMITES['topicos']}) — divida ou corte")
        for it in itens:
            txt = it.get("texto", "") if isinstance(it, dict) else str(it)
            pal = len(re.findall(r"\w+", re.sub(r"\[@[^\]]+\]", "", txt)))
            if pal > LIMITES["palavras_por_topico"]:
                self.avisos.append(f"slide {self.n}: tópico com {pal} palavras (máx. {LIMITES['palavras_por_topico']}) → \"{txt[:50]}...\"")
            self._registrar(txt)

    # ================================================================ layouts
    def capa(self, s):
        sl = self.novo(self.m.c["primaria"])
        self.forma(sl, W - 4.6, -1.8, 7.2, 7.2, self.m.c["secundaria"], MSO_SHAPE.OVAL, opacidade=0.35)
        self.forma(sl, W - 2.3, 4.9, 3.4, 3.4, self.m.c["destaque"], MSO_SHAPE.OVAL, opacidade=0.22)
        self._logo_capa(sl)
        titulo = self.t(s.get("titulo") or self.d.get("titulo", ""))
        tam = 40 if len(titulo) <= 60 else 34 if len(titulo) <= 95 else 28
        self.texto(sl, MX, 1.7, 9.3, 2.75, titulo, tamanho=tam, cor=self.m.c["texto_sobre_primaria"],
                   negrito=True, ancora="base", fonte=self.m.fonte_titulo, entre=0.95)
        self.forma(sl, MX, 4.62, 1.2, 0.07, self.m.c["destaque"])
        sub = s.get("subtitulo") or self.d.get("subtitulo")
        if sub:
            self.texto(sl, MX, 4.8, 9.3, 0.95, sub, tamanho=20,
                       cor=self.m.c["texto_sobre_primaria_suave"])
        autores = s.get("autores") or self.d.get("autores") or []
        if autores:
            self.texto(sl, MX, 5.85, 9.6, 0.42, " · ".join(autores), tamanho=16,
                       cor=self.m.c["texto_sobre_primaria"], negrito=True)
        info = [x for x in (s.get("curso") or self.d.get("curso"),
                            s.get("disciplina") or self.d.get("disciplina"),
                            s.get("orientador") or self.d.get("orientador"),
                            s.get("data") or self.d.get("data")) if x]
        if info:
            self.texto(sl, MX, 6.32, 10.5, 0.7, " · ".join(info), tamanho=13,
                       cor=self.m.c["texto_sobre_primaria_suave"])
        self.notas(sl, s)

    def _logo_capa(self, sl):
        caminho = self.m.arquivo("logo_negativo") or self.m.arquivo("logo")
        if caminho is None:
            self.texto(sl, MX, 0.55, 6, 0.6, f"**{self.m.d['sigla']}**  ·  {self.m.d['instituicao']}",
                       tamanho=16, cor=self.m.c["texto_sobre_primaria"],
                       realce=self.m.c["texto_sobre_primaria"])
            return
        from PIL import Image
        with Image.open(caminho) as im:
            prop = im.width / im.height
        h = 0.8
        w = min(h * prop, 4.0)
        h = w / prop
        self.logo(sl, MX + w, 0.6, h, escuro=True)

    def secao(self, s):
        sl = self.novo(self.m.c["primaria"])
        self.forma(sl, W - 3.4, -1.2, 5.0, 5.0, self.m.c["secundaria"], MSO_SHAPE.OVAL, opacidade=0.3)
        num = s.get("numero")
        if num is not None:
            self.texto(sl, MX, 1.9, 4, 1.4, f"{int(num):02d}" if str(num).isdigit() else str(num),
                       tamanho=80, cor=self.m.c["destaque"], negrito=True, fonte=self.m.fonte_titulo,
                       ancora="base")
        self.texto(sl, MX, 3.45, 10.5, 1.5, s["titulo"], tamanho=40, cor=self.m.c["texto_sobre_primaria"],
                   negrito=True, fonte=self.m.fonte_titulo)
        if s.get("subtitulo"):
            self.texto(sl, MX, 5.0, 10.5, 1.0, s["subtitulo"], tamanho=20,
                       cor=self.m.c["texto_sobre_primaria_suave"])
        self._registrar(s["titulo"])
        self.notas(sl, s)

    def topicos(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        itens = s.get("itens", [])
        self._checar_topicos(itens)
        n = len(itens)
        tam = 24 if n <= 3 else 22 if n == 4 else 20 if n == 5 else 18
        largura = W - 2 * MX
        if s.get("imagem"):
            largura = 6.9
            self._imagem_em(sl, s["imagem"], MX + 7.4, TOPO_CONTEUDO, W - 2 * MX - 7.4,
                            BASE_CONTEUDO - TOPO_CONTEUDO)
        elif s.get("destaque"):
            largura = 7.6
            self._cartao_destaque(sl, s["destaque"], MX + 8.1, TOPO_CONTEUDO + 0.2,
                                  W - 2 * MX - 8.1, 3.9)
        self.topicos_em(sl, MX, TOPO_CONTEUDO + 0.1, largura, BASE_CONTEUDO - TOPO_CONTEUDO, itens, tam)
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def _cartao_destaque(self, sl, d, x, y, w, h):
        self.forma(sl, x, y, w, h, self.m.c["fundo_suave"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.06)
        self.forma(sl, x, y, 0.09, h, self.m.c["secundaria"])
        self.texto(sl, x + 0.35, y + 0.3, w - 0.6, 1.4, d.get("valor", ""), tamanho=54,
                   cor=self.m.c["secundaria"], negrito=True, fonte=self.m.fonte_titulo, ancora="base")
        self.texto(sl, x + 0.35, y + 1.8, w - 0.6, h - 2.0, d.get("rotulo", ""), tamanho=16,
                   cor=self.m.c["texto"])

    def dois_colunas(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        gap = 0.4
        cw = (W - 2 * MX - gap) / 2
        h = BASE_CONTEUDO - TOPO_CONTEUDO
        for k, lado in enumerate(("esquerda", "direita")):
            col = s[lado]
            x = MX + k * (cw + gap)
            cor = self.m.c["secundaria"] if k == 0 else self.m.c["primaria"]
            self.forma(sl, x, TOPO_CONTEUDO, cw, h, self.m.c["fundo_suave"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.04)
            self.forma(sl, x, TOPO_CONTEUDO, cw, 0.09, cor)
            self.texto(sl, x + 0.35, TOPO_CONTEUDO + 0.3, cw - 0.7, 0.6, col.get("titulo", ""), tamanho=20,
                       cor=cor, negrito=True, fonte=self.m.fonte_titulo)
            itens = col.get("itens", [])
            self._checar_topicos(itens)
            self.topicos_em(sl, x + 0.35, TOPO_CONTEUDO + 1.05, cw - 0.7, h - 1.25, itens,
                            18 if len(itens) <= 4 else 16)
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def fluxo(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        etapas = s["etapas"]
        n = len(etapas)
        if not 2 <= n <= 6:
            raise ErroEntrada(f"slide {self.n}: 'fluxo' aceita de 2 a 6 etapas")
        seta = 0.5
        bw = (W - 2 * MX - (n - 1) * seta) / n
        t_tit = 20 if n <= 3 else 18 if n == 4 else 15
        t_desc = 17 if n <= 3 else 15 if n == 4 else 13
        norm = [{"titulo": e} if isinstance(e, str) else e for e in etapas]
        h_tit = max(altura_texto(e.get("titulo", ""), bw - 0.4, t_tit, 1.1) for e in norm)
        h_desc = max(altura_texto(e.get("texto", ""), bw - 0.4, t_desc) for e in norm)
        bh_max = 3.55 if s.get("conclusao") else 4.1
        bh = min(bh_max, max(2.2, 0.6 + h_tit + 0.25 + h_desc + 0.35))
        bloco = bh + (0.87 if s.get("conclusao") else 0)
        y = TOPO_CONTEUDO + 0.35 + max(0.0, (BASE_CONTEUDO - TOPO_CONTEUDO - 0.45 - bloco) / 2)
        for i, e in enumerate(etapas):
            x = MX + i * (bw + seta)
            self.forma(sl, x, y, bw, bh, self.m.c["fundo_suave"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.06)
            self.forma(sl, x + bw / 2 - 0.34, y - 0.34, 0.68, 0.68, self.m.c["primaria"], MSO_SHAPE.OVAL)
            self.texto(sl, x + bw / 2 - 0.34, y - 0.34, 0.68, 0.68, str(i + 1), tamanho=20,
                       cor=self.m.c["texto_sobre_primaria"], negrito=True, alinhar="centro", ancora="meio")
            e = norm[i]
            self.texto(sl, x + 0.2, y + 0.6, bw - 0.4, h_tit + 0.1, e.get("titulo", ""), tamanho=t_tit,
                       cor=self.m.c["primaria"], negrito=True, alinhar="centro", ancora="topo",
                       fonte=self.m.fonte_titulo, entre=1.0)
            if e.get("texto"):
                yt = y + 0.6 + h_tit + 0.25
                self.texto(sl, x + 0.2, yt, bw - 0.4, y + bh - yt - 0.15, e["texto"], tamanho=t_desc,
                           cor=self.m.c["texto"], alinhar="centro", realce=self.m.c["secundaria"])
            self._registrar(f"{e.get('titulo', '')} {e.get('texto', '')}")
            if i < n - 1:
                self.forma(sl, x + bw + 0.1, y + bh / 2 - 0.22, seta - 0.2, 0.44, self.m.c["secundaria"],
                           MSO_SHAPE.CHEVRON)
        if s.get("conclusao"):
            yc = y + bh + 0.25
            self.forma(sl, MX, yc, W - 2 * MX, 0.62, self.m.c["primaria"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.2)
            self.texto(sl, MX + 0.3, yc, W - 2 * MX - 0.6, 0.62, s["conclusao"], tamanho=16,
                       cor=self.m.c["texto_sobre_primaria"], negrito=True, alinhar="centro", ancora="meio")
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def numeros(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        mets = s["metricas"]
        n = len(mets)
        if not 1 <= n <= 3:
            raise ErroEntrada(f"slide {self.n}: 'numeros' aceita de 1 a 3 métricas")
        gap = 0.5
        cw = (W - 2 * MX - (n - 1) * gap) / n
        tv = 88 if n == 1 else 66 if n == 2 else 54
        y = TOPO_CONTEUDO + (0.5 if s.get("texto") else 0.8)
        for i, m in enumerate(mets):
            x = MX + i * (cw + gap)
            if n > 1:
                self.forma(sl, x, y - 0.1, cw, 3.3, self.m.c["fundo_suave"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.05)
            self.texto(sl, x + 0.2, y, cw - 0.4, 1.55, m["valor"], tamanho=tv, cor=self.m.c["secundaria"],
                       negrito=True, alinhar="centro", ancora="base", fonte=self.m.fonte_titulo)
            self.texto(sl, x + 0.3, y + 1.65, cw - 0.6, 0.55, m.get("rotulo", ""), tamanho=19,
                       cor=self.m.c["primaria"], negrito=True, alinhar="centro")
            if m.get("detalhe"):
                self.texto(sl, x + 0.3, y + 2.2, cw - 0.6, 0.9, m["detalhe"], tamanho=14,
                           cor=self.m.c["texto_suave"], alinhar="centro")
        if s.get("texto"):
            self.texto(sl, MX, 5.75, W - 2 * MX, 0.8, s["texto"], tamanho=18, cor=self.m.c["texto"],
                       alinhar="centro", ancora="meio", realce=self.m.c["primaria"])
            self._registrar(s["texto"])
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def tabela(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        cols, linhas = s["colunas"], s["linhas"]
        nl = len(linhas)
        if nl > 7:
            self.avisos.append(f"slide {self.n}: tabela com {nl} linhas — no slide, prefira até 6")
        tam = 15 if nl <= 4 else 13 if nl <= 6 else 11
        larg_total = W - 2 * MX
        altura_linha = 0.5 if nl <= 5 else 0.42
        shp = sl.shapes.add_table(nl + 1, len(cols), Inches(MX), Inches(TOPO_CONTEUDO + 0.1),
                                  Inches(larg_total), Inches(altura_linha * (nl + 1)))
        tbl = shp.table
        tbl.first_row = True
        tbl.horz_banding = False
        pesos = s.get("larguras") or [
            max(6, min(40, max(len(str(r[j])) for r in [cols] + linhas))) for j in range(len(cols))]
        soma = sum(pesos)
        for j, p in enumerate(pesos):
            tbl.columns[j].width = Inches(larg_total * p / soma)
        for i in range(nl + 1):
            tbl.rows[i].height = Inches(altura_linha)
            for j in range(len(cols)):
                cel = tbl.cell(i, j)
                valor = cols[j] if i == 0 else linhas[i - 1][j]
                cel.fill.solid()
                cel.fill.fore_color.rgb = (self.m.c["primaria"] if i == 0 else
                                           self.m.c["fundo_suave"] if i % 2 == 0 else self.m.c["fundo"])
                cel.margin_left = cel.margin_right = Inches(0.12)
                cel.margin_top = cel.margin_bottom = Inches(0.06)
                cel.vertical_anchor = MSO_ANCHOR.MIDDLE
                tf = cel.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                self._runs(p, self.t(str(valor)), tam,
                           self.m.c["texto_sobre_primaria"] if i == 0 else self.m.c["texto"],
                           i == 0 or (j == 0 and s.get("primeira_coluna_negrito", True)), False, None,
                           self.m.c["primaria"])
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def picos(self, s):
        sl = self.novo()
        self.titulo(sl, s.get("titulo", "Pergunta de pesquisa"))
        rotulos = {"P": "População", "I": "Intervenção", "C": "Comparação", "O": "Desfecho",
                   "S": "Tipo de estudo", "E": "Exposição", "Co": "Contexto", "T": "Tempo"}
        elementos = s.get("elementos")
        if not elementos:
            elementos = [{"letra": k, "rotulo": rotulos.get(k, k), "texto": s[k]}
                         for k in ("P", "I", "C", "O", "S") if s.get(k)]
        n = len(elementos)
        gap = 0.3
        cw = (W - 2 * MX - (n - 1) * gap) / n
        y = TOPO_CONTEUDO + 0.1
        t_txt = 18 if n <= 4 else 16
        h_txt = max(altura_texto(e["texto"], cw - 0.4, t_txt) for e in elementos)
        ch = min(3.15 if s.get("pergunta") else 4.3, max(2.4, 1.75 + h_txt + 0.3))
        for i, e in enumerate(elementos):
            x = MX + i * (cw + gap)
            self.forma(sl, x, y, cw, ch, self.m.c["fundo_suave"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.05)
            self.forma(sl, x, y, cw, 0.95, self.m.c["primaria"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.12)
            self.forma(sl, x, y + 0.5, cw, 0.45, self.m.c["primaria"])
            self.texto(sl, x, y + 0.05, cw, 0.85, e["letra"], tamanho=36, cor=self.m.c["texto_sobre_primaria"],
                       negrito=True, alinhar="centro", ancora="meio", fonte=self.m.fonte_titulo)
            self.texto(sl, x + 0.2, y + 1.1, cw - 0.4, 0.45, e.get("rotulo", rotulos.get(e["letra"], "")),
                       tamanho=15, cor=self.m.c["secundaria"], negrito=True, alinhar="centro")
            self.texto(sl, x + 0.2, y + 1.65, cw - 0.4, ch - 1.75, e["texto"], tamanho=t_txt,
                       cor=self.m.c["texto"], alinhar="centro")
        if s.get("pergunta"):
            yp = y + ch + 0.35
            self.forma(sl, MX, yp, W - 2 * MX, 1.05, self.m.c["fundo_suave"])
            self.forma(sl, MX, yp, 0.09, 1.05, self.m.c["destaque"])
            self.texto(sl, MX + 0.35, yp, W - 2 * MX - 0.6, 1.05, s["pergunta"], tamanho=18,
                       cor=self.m.c["texto"], italico=True, ancora="meio")
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    CERTEZA = {"alta": ("●●●● Alta", "secundaria"), "moderada": ("●●●○ Moderada", "primaria"),
               "baixa": ("●●○○ Baixa", "destaque"), "muito baixa": ("●○○○ Muito baixa", "texto_suave")}

    def evidencias(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        linhas = s["estudos"]
        n = len(linhas)
        if n > 5:
            self.avisos.append(f"slide {self.n}: {n} estudos — mostre no máximo 5 por slide")
        area = BASE_CONTEUDO - TOPO_CONTEUDO
        rh = min(1.1, area / max(n, 1))
        for i, e in enumerate(linhas):
            y = TOPO_CONTEUDO + 0.05 + i * rh
            self.forma(sl, MX, y + 0.12, 1.55, rh - 0.24, self.m.c["primaria"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.15)
            self.texto(sl, MX, y + 0.12, 1.55, rh - 0.24, e.get("desenho", ""), tamanho=13,
                       cor=self.m.c["texto_sobre_primaria"], negrito=True, alinhar="centro", ancora="meio")
            corpo = []
            if e.get("estudo"):
                corpo.append(f"**{self.t(e['estudo'])}**")
            corpo_txt = " — ".join(corpo + [e.get("achado", "")]) if corpo else e.get("achado", "")
            self.texto(sl, MX + 1.8, y + 0.08, W - 2 * MX - 4.2, rh - 0.16, corpo_txt,
                       tamanho=15 if n <= 4 else 14, cor=self.m.c["texto"], ancora="meio",
                       realce=self.m.c["primaria"])
            self._registrar(e.get("achado", ""))
            cert = (e.get("certeza") or "").lower().strip()
            if cert:
                rot, chave = self.CERTEZA.get(cert, (e["certeza"], "texto_suave"))
                self.forma(sl, W - MX - 2.15, y + rh / 2 - 0.24, 2.15, 0.48, self.m.c[chave],
                           MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.5)
                self.texto(sl, W - MX - 2.15, y + rh / 2 - 0.24, 2.15, 0.48, rot, tamanho=12,
                           cor=self.m.c["texto_sobre_primaria"], negrito=True, alinhar="centro", ancora="meio")
            if i < n - 1:
                self.forma(sl, MX, y + rh - 0.01, W - 2 * MX, 0.015, self.m.c["fundo_suave"])
        if any(e.get("certeza") for e in linhas):
            self.texto(sl, W - MX - 4.5, 6.62, 4.5, 0.25, "Certeza da evidência: GRADE", tamanho=9,
                       cor=self.m.c["texto_suave"], alinhar="dir")
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def mensagem(self, s):
        sl = self.novo()
        if s.get("titulo"):
            self.titulo(sl, s["titulo"])
        self.texto(sl, MX + 0.4, 1.9, 1.0, 1.2, "“", tamanho=110, cor=self.m.c["secundaria"],
                   negrito=True, fonte="Georgia")
        self.texto(sl, MX + 1.4, 2.25, W - 2 * MX - 2.4, 3.2, s["texto"], tamanho=30 if len(s["texto"]) < 140 else 24,
                   cor=self.m.c["primaria"], ancora="meio", fonte=self.m.fonte_titulo, realce=self.m.c["secundaria"])
        if s.get("autor"):
            self.texto(sl, MX + 1.4, 5.6, W - 2 * MX - 2.4, 0.5, f"— {s['autor']}", tamanho=16,
                       cor=self.m.c["texto_suave"])
        self._registrar(s["texto"])
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def conclusao(self, s):
        sl = self.novo()
        self.titulo(sl, s.get("titulo", "Mensagens-chave"))
        itens = s["itens"]
        self._checar_topicos(itens)
        n = len(itens)
        if n > 4:
            self.avisos.append(f"slide {self.n}: {n} mensagens-chave — mantenha até 4")
        grade = (2, 2) if n == 4 else (1, n)
        linhas, cols = grade
        gap = 0.35
        cw = (W - 2 * MX - (cols - 1) * gap) / cols
        area = BASE_CONTEUDO - TOPO_CONTEUDO - 0.1
        ch = (area - (linhas - 1) * gap) / linhas
        for i, it in enumerate(itens):
            r, c = divmod(i, cols)
            x = MX + c * (cw + gap)
            y = TOPO_CONTEUDO + 0.1 + r * (ch + gap)
            self.forma(sl, x, y, cw, ch, self.m.c["fundo_suave"], MSO_SHAPE.ROUNDED_RECTANGLE, raio=0.05)
            self.forma(sl, x + 0.3, y + 0.3, 0.62, 0.62, self.m.c["secundaria"], MSO_SHAPE.OVAL)
            self.texto(sl, x + 0.3, y + 0.3, 0.62, 0.62, str(i + 1), tamanho=18,
                       cor=self.m.c["texto_sobre_primaria"], negrito=True, alinhar="centro", ancora="meio")
            if linhas == 1:
                self.texto(sl, x + 0.3, y + 1.15, cw - 0.6, ch - 1.35, it, tamanho=19,
                           cor=self.m.c["texto"], realce=self.m.c["primaria"])
            else:
                self.texto(sl, x + 1.15, y + 0.25, cw - 1.45, ch - 0.5, it, tamanho=19,
                           cor=self.m.c["texto"], ancora="meio", realce=self.m.c["primaria"])
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def _imagem_em(self, sl, caminho, x, y, w, h):
        p = (self.base / caminho).resolve()
        if not p.exists():
            raise ErroEntrada(f"imagem não encontrada: {p}")
        from PIL import Image
        with Image.open(p) as im:
            prop = im.width / im.height
        if w / h > prop:
            iw, ih = h * prop, h
        else:
            iw, ih = w, w / prop
        sl.shapes.add_picture(str(p), Inches(x + (w - iw) / 2), Inches(y + (h - ih) / 2),
                              Inches(iw), Inches(ih))

    def imagem(self, s):
        sl = self.novo()
        self.titulo(sl, s["titulo"])
        alt = BASE_CONTEUDO - TOPO_CONTEUDO - (0.5 if s.get("legenda") else 0)
        self._imagem_em(sl, s["imagem"], MX, TOPO_CONTEUDO, W - 2 * MX, alt)
        if s.get("legenda"):
            self.texto(sl, MX, BASE_CONTEUDO - 0.4, W - 2 * MX, 0.4, s["legenda"], tamanho=14,
                       cor=self.m.c["texto_suave"], alinhar="centro")
        self.rodape(sl, s.get("fonte"))
        self.notas(sl, s)

    def referencias(self, s):
        ids = s.get("ids")
        citadas_slides = list(self.cit.citadas)
        if ids:
            lista = [r for r in self.refs if r["id"] in ids]
        elif s.get("todas"):
            lista = self.refs
        else:
            lista = [r for r in self.refs if r["id"] in citadas_slides]
        if not lista:
            self.avisos.append("slide de referências sem referências (nenhuma citada nos slides)")
            return
        por_slide, atual, tamanho = [], [], 0
        for r in lista:
            txt = abnt.referencia_texto(r)
            if atual and (tamanho + len(txt) > 1900 or len(atual) >= 8):
                por_slide.append(atual)
                atual, tamanho = [], 0
            atual.append(r)
            tamanho += len(txt)
        por_slide.append(atual)
        for k, grupo in enumerate(por_slide, start=1):
            sl = self.novo()
            tit = s.get("titulo", "Referências")
            if len(por_slide) > 1:
                tit += f" ({k}/{len(por_slide)})"
            self.texto(sl, MX, 0.42, W - 2 * MX, 1.05, tit, tamanho=30, cor=self.m.c["primaria"],
                       negrito=True, ancora="base", fonte=self.m.fonte_titulo)
            self.forma(sl, MX, 1.6, 0.9, 0.07, self.m.c["secundaria"])
            tb = sl.shapes.add_textbox(Inches(MX), Inches(TOPO_CONTEUDO), Inches(W - 2 * MX),
                                       Inches(BASE_CONTEUDO - TOPO_CONTEUDO))
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Emu(0)
            for i, r in enumerate(grupo):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.space_after = Pt(9)
                for txt, est in abnt.referencia_segmentos(r):
                    run = p.add_run()
                    run.text = txt
                    run.font.size = Pt(12.5)
                    run.font.name = self.m.fonte_corpo
                    run.font.bold = est == "b"
                    run.font.italic = est == "i"
                    run.font.color.rgb = self.m.c["texto"]
            self.rodape(sl)
            self.notas(sl, s)

    def encerramento(self, s):
        sl = self.novo(self.m.c["primaria"])
        self.forma(sl, -2.0, 3.6, 6.0, 6.0, self.m.c["secundaria"], MSO_SHAPE.OVAL, opacidade=0.3)
        self.texto(sl, MX, 2.0, W - 2 * MX, 1.4, s.get("titulo", "Obrigado!"), tamanho=56,
                   cor=self.m.c["texto_sobre_primaria"], negrito=True, alinhar="centro", ancora="base",
                   fonte=self.m.fonte_titulo)
        self.forma(sl, W / 2 - 0.6, 3.6, 1.2, 0.07, self.m.c["destaque"])
        if s.get("texto"):
            self.texto(sl, MX + 1, 3.85, W - 2 * MX - 2, 1.2, s["texto"], tamanho=20,
                       cor=self.m.c["texto_sobre_primaria_suave"], alinhar="centro")
        if s.get("contato"):
            self.texto(sl, MX, 5.1, W - 2 * MX, 0.5, s["contato"], tamanho=16,
                       cor=self.m.c["texto_sobre_primaria"], alinhar="centro")
        caminho = self.m.arquivo("logo_negativo") or self.m.arquivo("logo")
        if caminho:
            from PIL import Image
            with Image.open(caminho) as im:
                prop = im.width / im.height
            h = 0.7
            w = min(h * prop, 3.5)
            h = w / prop
            self.logo(sl, W / 2 + w / 2, 6.0, h, escuro=True)
        else:
            self.texto(sl, MX, 6.1, W - 2 * MX, 0.5, f"**{self.m.d['sigla']}** · {self.m.d['instituicao']}",
                       tamanho=14, cor=self.m.c["texto_sobre_primaria"], alinhar="centro",
                       realce=self.m.c["texto_sobre_primaria"])
        self.notas(sl, s)

    # ================================================================ fluxo
    def gerar(self, saida: Path) -> dict:
        slides = self.d.get("slides") or []
        if not slides:
            raise ErroEntrada("'slides' vazio")
        # Referências ficam por último para listar o que foi citado nos slides anteriores.
        for s in slides:
            layout = s.get("layout", "topicos")
            fn = getattr(self, layout, None)
            if fn is None or layout.startswith("_"):
                raise ErroEntrada(f"layout desconhecido: {layout}")
            fn(s)
        if not (self.m.arquivo("logo") or self.m.arquivo("logo_negativo")):
            self.avisos.insert(0, "logo da FPS não encontrado em marca/ — usando marcador de texto")
        saida.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(str(saida))
        return {"arquivo": str(saida), "slides": len(self.prs.slides),
                "citacoes_sem_referencia": self.cit.ausentes, "avisos": self.avisos}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json", type=Path)
    ap.add_argument("-o", "--saida", type=Path)
    ap.add_argument("--marca", type=Path, help="marca JSON (padrão: marca/marca-fps.json)")
    a = ap.parse_args()
    dados = json.loads(a.json.read_text(encoding="utf-8"))
    base = a.json.parent
    marca_path = a.marca or (base / dados["marca"] if dados.get("marca") else RAIZ / "marca" / "marca-fps.json")
    marca = Marca(marca_path, dados.get("marca_sobrescrever"))
    refs = []
    if dados.get("referencias_arquivo"):
        refs = abnt.carregar_referencias(base / dados["referencias_arquivo"])
    try:
        res = Construtor(dados, base, marca, refs).gerar(a.saida or a.json.with_suffix(".pptx"))
    except (ErroEntrada, KeyError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 1 if res["citacoes_sem_referencia"] else 0


if __name__ == "__main__":
    sys.exit(main())
