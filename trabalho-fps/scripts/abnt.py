"""Regras ABNT compartilhadas pelos geradores (DOCX, PPTX e validador).

- Referências: ABNT NBR 6023:2018.
- Citações (sistema autor-data): ABNT NBR 10520:2023 (padrão) ou 2002.

Formato de cada referência (lista em referencias.json):

    {
      "id": "page2021",                       # chave usada no texto: [@page2021]
      "tipo": "artigo",                       # artigo | livro | capitulo | documento | guideline | site
      "autores": ["Page, Matthew J.", "McKenzie, Joanne E."],  # "Sobrenome, Prenomes" (ou "Page MJ")
      "et_al": false,                         # true = há mais autores do que os listados
      "autor_entidade": null,                 # ex.: "World Health Organization", "Brasil. Ministério da Saúde"
      "citar_como": null,                     # opcional: força o texto da chamada (ex.: "OMS")
      "titulo": "...", "subtitulo": null,
      "periodico": "BMJ",                     # artigo
      "local": "London", "editora": "...", "edicao": "3",   # livros/documentos
      "in_autores": [], "in_papel": "org.", "in_titulo": "",   # capítulo de livro
      "ano": 2021, "mes": null, "volume": "372", "numero": null,
      "paginas": "n71",                       # intervalo '924-926' vira 'p. 924-926';
                                              # valor único ('n71', 'e0234') = nº do artigo
      "paginas_total": null, "serie": null,   # livros/documentos (opcionais)
      "doi": "10.1136/bmj.n71", "pmid": "33782057", "url": null, "acesso": "2026-11-09",
      "desenho": "Diretriz metodológica", "nivel_evidencia": null,
      "verificado": true, "verificado_via": "PubMed PMID 33782057"
    }
"""
from __future__ import annotations

import datetime as _dt
import re
import unicodedata

MESES = ["jan.", "fev.", "mar.", "abr.", "maio", "jun.",
         "jul.", "ago.", "set.", "out.", "nov.", "dez."]

PARTICULAS = {"de", "da", "do", "das", "dos", "e", "del", "van", "von", "der",
              "den", "di", "du", "la", "le", "y"}
SUFIXOS = {"filho", "filha", "junior", "júnior", "jr", "neto", "neta",
           "sobrinho", "sobrinha"}

Segmento = tuple[str, str]  # (texto, estilo) estilo: "" | "b" | "i"


class ErroReferencia(ValueError):
    pass


# --------------------------------------------------------------------------- util

def sem_acento(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def data_acesso(valor) -> str:
    """'2026-11-09' -> '9 nov. 2026' (NBR 6023)."""
    if not valor:
        d = _dt.date.today()
    elif isinstance(valor, _dt.date):
        d = valor
    else:
        try:
            d = _dt.date.fromisoformat(str(valor)[:10])
        except ValueError:
            return str(valor)
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def _ponto_final(s: str) -> str:
    s = s.rstrip()
    return s if s.endswith((".", "?", "!")) else s + "."


def _fecha_titulo(s: str) -> str:
    """Título seguido de ponto, sem duplicar quando já termina em ? ou ! (evita 'matter?.')."""
    s = s.rstrip()
    return s + " " if s.endswith(("?", "!")) else s + ". "


# ------------------------------------------------------------------------ autores

def parse_autor(autor: str) -> tuple[str, str]:
    """Retorna (sobrenome, iniciais) a partir de 'Sobrenome, Prenomes',
    'Sobrenome AB' (Vancouver/PubMed) ou 'Prenomes Sobrenome'."""
    s = " ".join(str(autor).split())
    if "," in s:
        sob, pre = s.split(",", 1)
        return sob.strip(), iniciais(pre.strip())
    toks = s.split(" ")
    if len(toks) >= 2 and re.fullmatch(r"[A-ZÀ-Ý]{1,4}", toks[-1]):
        return " ".join(toks[:-1]), " ".join(c + "." for c in toks[-1])
    if len(toks) >= 3 and toks[-1].lower().strip(".") in SUFIXOS:
        return " ".join(toks[-2:]), iniciais(" ".join(toks[:-2]))
    if len(toks) >= 2:
        return toks[-1], iniciais(" ".join(toks[:-1]))
    return s, ""


def iniciais(prenomes: str) -> str:
    out = []
    for tok in prenomes.replace(".", ". ").split():
        t = tok.strip().strip(".")
        if not t or t.lower() in PARTICULAS:
            continue
        if "-" in t:
            out.append("-".join(p[0].upper() + "." for p in t.split("-") if p))
        else:
            out.append(t[0].upper() + ".")
    return " ".join(out)


def _sobrenome_citacao(sob: str) -> str:
    """Sobrenome em maiúsculas e minúsculas (NBR 10520:2023)."""
    if sob.isupper() and len(sob) > 3:
        partes = []
        for p in sob.split(" "):
            partes.append(p.lower() if p.lower() in PARTICULAS else p.capitalize())
        return " ".join(partes)
    return sob


def entidade_referencia(entidade: str) -> str:
    """'Brasil. Ministério da Saúde' -> 'BRASIL. Ministério da Saúde'."""
    partes = entidade.split(". ")
    partes[0] = partes[0].upper()
    return ". ".join(partes)


def _autores_referencia(ref: dict, cfg: dict) -> str | None:
    if ref.get("autor_entidade"):
        return _ponto_final(entidade_referencia(ref["autor_entidade"]))
    autores = ref.get("autores") or []
    if not autores:
        return None
    parsed = [parse_autor(a) for a in autores]
    fmt = [f"{s.upper()}, {i}".rstrip(", ") if i else s.upper() for s, i in parsed]
    muitos = len(fmt) > 3 or ref.get("et_al")
    if muitos and (cfg.get("autores_referencia", "et_al") == "et_al" or ref.get("et_al")):
        return f"{fmt[0]} et al."
    return _ponto_final("; ".join(fmt))


def _lista_in(autores: list, papel: str | None) -> str:
    parsed = [parse_autor(a) for a in autores]
    fmt = [f"{s.upper()}, {i}".rstrip(", ") if i else s.upper() for s, i in parsed]
    if len(fmt) > 3:
        txt = f"{fmt[0]} et al."
    else:
        txt = "; ".join(fmt)
    return f"{txt} ({papel or 'org.'})."


# -------------------------------------------------------------------- referências

def _paginas(p) -> str | None:
    """'924-926' ou 'E839-E842' -> 'p. 924-926'. Um valor único sem intervalo
    ('n71', 'e0234', '579') é tratado como número do artigo eletrônico e sai
    como está; para página única escreva 'p. 5'."""
    if not p:
        return None
    p = str(p).strip().replace("–", "-").replace("—", "-")
    if re.fullmatch(r"[A-Za-z]?\d+\s*-\s*[A-Za-z]?\d+", p):
        return "p. " + re.sub(r"\s*-\s*", "-", p)
    return p


def _edicao(ed) -> str | None:
    if not ed:
        return None
    ed = str(ed).strip()
    if ed in {"1", "1."}:
        return None
    return ed if "ed" in ed else f"{ed.rstrip('.')}. ed."


def _acesso_online(ref: dict) -> list[Segmento]:
    segs: list[Segmento] = []
    if ref.get("doi"):
        doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", str(ref["doi"]).strip())
        segs.append((f" DOI: {doi}.", ""))
    url = ref.get("url")
    if not url and not ref.get("doi") and ref.get("pmid"):
        url = f"https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/"
    if url:
        segs.append((f" Disponível em: {url}. Acesso em: {data_acesso(ref.get('acesso'))}.", ""))
    return segs


def ano_exibido(ref: dict) -> str:
    ano = str(ref.get("ano") or "[s. d.]")
    return ano + ref.get("_sufixo_ano", "")


def referencia_segmentos(ref: dict, cfg: dict | None = None) -> list[Segmento]:
    """Monta a referência em segmentos (texto, estilo) para aplicar destaque."""
    cfg = cfg or {}
    destaque = "i" if cfg.get("destaque") == "italico" else "b"
    tipo = (ref.get("tipo") or "artigo").lower()
    autores = _autores_referencia(ref, cfg)
    titulo = (ref.get("titulo") or "").strip().rstrip(".")
    sub = (ref.get("subtitulo") or "").strip().rstrip(".")
    ano = ano_exibido(ref)
    segs: list[Segmento] = []

    def titulo_sem_autor(destacar: bool) -> None:
        # Entrada pelo título: primeira palavra em maiúsculas, sem destaque.
        partes = titulo.split(" ", 1)
        t = partes[0].upper() + (" " + partes[1] if len(partes) > 1 else "")
        segs.append((_fecha_titulo(t + (f": {sub}" if sub else "")), ""))

    if tipo == "artigo":
        if autores:
            segs.append((autores + " ", ""))
            segs.append((_fecha_titulo(titulo + (f": {sub}" if sub else "")), ""))
        else:
            titulo_sem_autor(False)
        if not ref.get("periodico"):
            raise ErroReferencia(f"[{ref.get('id')}] artigo sem 'periodico'")
        segs.append((ref["periodico"].strip(), destaque))
        resto = []
        if ref.get("local"):
            resto.append(ref["local"])
        if ref.get("volume"):
            resto.append(f"v. {ref['volume']}")
        if ref.get("numero"):
            resto.append(f"n. {ref['numero']}")
        pg = _paginas(ref.get("paginas"))
        if pg:
            resto.append(pg)
        resto.append(f"{ref['mes']} {ano}" if ref.get("mes") else ano)
        segs.append((", " + ", ".join(resto) + ".", ""))
        segs += _acesso_online(ref)
    elif tipo == "capitulo":
        segs.append(((autores or "") + " ", ""))
        segs.append((_fecha_titulo(titulo + (f": {sub}" if sub else "")), ""))
        segs.append(("In: ", ""))
        if ref.get("in_autores"):
            segs.append((_lista_in(ref["in_autores"], ref.get("in_papel")) + " ", ""))
        segs.append(((ref.get("in_titulo") or "").strip().rstrip("."), destaque))
        segs.append((". ", ""))
        ed = _edicao(ref.get("edicao"))
        if ed:
            segs.append((ed + " ", ""))
        segs.append((_imprenta(ref, ano) + ".", ""))
        pg = _paginas(ref.get("paginas"))
        if pg:
            segs.append((f" {pg}.", ""))
        segs += _acesso_online(ref)
    else:  # livro, documento, guideline, site, legislação, relatório
        if autores:
            segs.append((autores + " ", ""))
            segs.append((titulo, destaque))
            segs.append(((f": {sub}" if sub else "") + ". ", ""))
        else:
            titulo_sem_autor(False)
        ed = _edicao(ref.get("edicao"))
        if ed:
            segs.append((ed + " ", ""))
        if tipo == "site":
            loc = ref.get("local")
            segs.append(((f"{loc}, {ano}" if loc else ano) + ".", ""))
        else:
            segs.append((_imprenta(ref, ano) + ".", ""))
        if ref.get("paginas_total"):
            segs.append((f" {ref['paginas_total']} p.", ""))
        if ref.get("serie"):
            segs.append((f" ({ref['serie']}).", ""))
        segs += _acesso_online(ref)
    # Junta segmentos vizinhos de mesmo estilo e normaliza espaços.
    out: list[Segmento] = []
    for txt, st in segs:
        if not txt:
            continue
        if out and out[-1][1] == st:
            out[-1] = (out[-1][0] + txt, st)
        else:
            out.append((txt, st))
    out = [(re.sub(r"\s{2,}", " ", t).replace(" .", ".").replace("..", "."), s) for t, s in out]
    if out:
        out[-1] = (out[-1][0].rstrip(), out[-1][1])
    return out


def _imprenta(ref: dict, ano: str) -> str:
    local = ref.get("local")
    editora = ref.get("editora")
    if local and editora:
        return f"{local}: {editora}, {ano}"
    if local:
        return f"{local}: [s. n.], {ano}"
    if editora:
        return f"[S. l.]: {editora}, {ano}"
    return f"[S. l.: s. n.], {ano}"


def referencia_texto(ref: dict, cfg: dict | None = None) -> str:
    return "".join(t for t, _ in referencia_segmentos(ref, cfg))


# ---------------------------------------------------------------------- citações

def _nomes_citacao(ref: dict) -> tuple[list[str], bool]:
    if ref.get("citar_como"):
        return [ref["citar_como"]], False
    if ref.get("autor_entidade"):
        return [ref["autor_entidade"].split(". ")[0]], False
    autores = ref.get("autores") or []
    if autores:
        nomes = [_sobrenome_citacao(parse_autor(a)[0]) for a in autores]
        return nomes, bool(ref.get("et_al")) or len(nomes) > 3
    primeira = (ref.get("titulo") or "?").split(" ")[0]
    return [primeira.capitalize() + "..."], False


def rotulo_autoria(ref: dict, narrativa: bool = False, estilo: str = "2023") -> str:
    nomes, et_al = _nomes_citacao(ref)
    if et_al:
        base = f"{nomes[0]} et al."
        if estilo == "2002" and not narrativa:
            base = f"{nomes[0].upper()} et al."
        return base
    if estilo == "2002" and not narrativa:
        nomes = [n.upper() for n in nomes]
    if len(nomes) == 1:
        return nomes[0]
    if narrativa:
        return ", ".join(nomes[:-1]) + " e " + nomes[-1]
    return "; ".join(nomes)


def ordenar_e_desambiguar(refs: list[dict], cfg: dict | None = None) -> list[dict]:
    """Ordena alfabeticamente (NBR 6023) e acrescenta a/b/c ao ano quando
    há mesma autoria e mesmo ano (ex.: Silva, 2020a; Silva, 2020b)."""
    cfg = cfg or {}

    def chave(r: dict):
        ent = _autores_referencia(r, cfg) or (r.get("titulo") or "")
        return (sem_acento(ent).lower(), str(r.get("ano") or ""),
                sem_acento(r.get("titulo") or "").lower())

    ordenadas = sorted(refs, key=chave)
    grupos: dict[tuple, list[dict]] = {}
    for r in ordenadas:
        r.pop("_sufixo_ano", None)
        k = (rotulo_autoria(r), str(r.get("ano")))
        grupos.setdefault(k, []).append(r)
    for lst in grupos.values():
        if len(lst) > 1:
            for i, r in enumerate(lst):
                r["_sufixo_ano"] = "abcdefghijklmnopqrstuvwxyz"[i]
    return ordenadas


class Citador:
    """Substitui marcadores de citação no texto.

    [@id]              -> (Silva, 2020)
    [@id1; @id2]       -> (Silva, 2020; Souza; Lima, 2021)
    [@id, p. 34]       -> (Silva, 2020, p. 34)
    @id                -> Silva (2020)          (citação narrativa)
    """

    RE_GRUPO = re.compile(r"\[\s*(@[^\[\]]+?)\s*\]")
    RE_ITEM = re.compile(r"@([A-Za-z0-9][\w:-]*)\s*(?:,\s*(.+))?$")
    RE_NARR = re.compile(r"(?<![\w.@/\[])@([A-Za-z0-9][\w:-]*[A-Za-z0-9]|[A-Za-z0-9])")

    def __init__(self, refs: list[dict], estilo: str = "2023"):
        self.estilo = estilo
        self.por_id: dict[str, dict] = {}
        for r in refs:
            self.por_id[r["id"]] = r
            for a in r.get("aliases", []) or []:
                self.por_id.setdefault(a, r)
        self.citadas: list[str] = []
        self.ausentes: list[str] = []

    def _ref(self, rid: str) -> dict | None:
        r = self.por_id.get(rid)
        if r is None:
            if rid not in self.ausentes:
                self.ausentes.append(rid)
            return None
        if r["id"] not in self.citadas:
            self.citadas.append(r["id"])
        return r

    def parenteses(self, ids_locais: list[tuple[str, str | None]]) -> str:
        partes = []
        for rid, loc in ids_locais:
            r = self._ref(rid)
            if r is None:
                partes.append(f"??{rid}??")
                continue
            p = f"{rotulo_autoria(r, False, self.estilo)}, {ano_exibido(r)}"
            if loc:
                p += f", {loc.strip()}"
            partes.append(p)
        return "(" + "; ".join(partes) + ")"

    def narrativa(self, rid: str) -> str:
        r = self._ref(rid)
        if r is None:
            return f"??{rid}??"
        return f"{rotulo_autoria(r, True, self.estilo)} ({ano_exibido(r)})"

    def curta(self, rid: str) -> str:
        """Ex.: 'Page et al., 2021' (sem parênteses), para rodapés de slide."""
        r = self._ref(rid)
        if r is None:
            return f"??{rid}??"
        return f"{rotulo_autoria(r, False, self.estilo)}, {ano_exibido(r)}"

    def aplicar(self, texto: str) -> str:
        if not texto or "@" not in texto:
            return texto

        def grupo(m: re.Match) -> str:
            itens = []
            for parte in m.group(1).split(";"):
                mm = self.RE_ITEM.match(parte.strip())
                if not mm:
                    return m.group(0)
                itens.append((mm.group(1), mm.group(2)))
            return self.parenteses(itens)

        texto = self.RE_GRUPO.sub(grupo, texto)
        return self.RE_NARR.sub(lambda m: self.narrativa(m.group(1)), texto)


def ids_citados(texto: str) -> list[str]:
    """Lista os ids citados em um texto (sem resolver)."""
    if not texto or "@" not in texto:
        return []
    ids = []
    for m in Citador.RE_GRUPO.finditer(texto):
        for parte in m.group(1).split(";"):
            mm = Citador.RE_ITEM.match(parte.strip())
            if mm:
                ids.append(mm.group(1))
    resto = Citador.RE_GRUPO.sub(" ", texto)
    ids += [m.group(1) for m in Citador.RE_NARR.finditer(resto)]
    return ids


def carregar_referencias(caminho) -> list[dict]:
    import json
    from pathlib import Path
    dados = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if isinstance(dados, dict):
        dados = dados.get("referencias", [])
    vistos = set()
    for r in dados:
        if "id" not in r:
            raise ErroReferencia(f"referência sem 'id': {r.get('titulo')}")
        if r["id"] in vistos:
            raise ErroReferencia(f"id duplicado em {caminho}: {r['id']}")
        vistos.add(r["id"])
    return dados
