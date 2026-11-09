#!/usr/bin/env python3
"""Pareceres de revisão, portões de qualidade e memória de lições do pipeline FPS.

Os revisores (modelos mais capazes) avaliam o trabalho dos executores (modelos mais
básicos) e gravam um parecer JSON. Este script decide — de forma determinística —
se a etapa está APROVADA, volta para REVISAR ou deve ser ESCALADA ao revisor.

Uso:
  python3 parecer.py modelo <etapa>                      # imprime um parecer em branco
  python3 parecer.py avaliar <arquivo.parecer.json>       # valida e aplica o portão
  python3 parecer.py resposta <resposta.json> <parecer.json>  # confere a resposta do executor
  python3 parecer.py painel <pasta-do-trabalho>           # gera painel.md (status de todas as etapas)
  python3 parecer.py licoes <pasta-do-trabalho>           # consolida lições na memória do pipeline

Códigos de saída de 'avaliar': 0 = APROVADO · 1 = REVISAR · 3 = ESCALAR · 2 = parecer inválido.

Portão (aprovação): nenhum achado 'critica' ou 'maior', média dos critérios >= 7,5
e nenhum critério < 6. Na 3ª rodada sem aprovação → ESCALAR (o revisor corrige direto).
"""
from __future__ import annotations

import datetime as dt
import difflib
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEMORIA = Path(os.environ.get("FPS_MEMORIA", RAIZ / "memoria"))
MEDIA_MINIMA = 7.5
NOTA_MINIMA = 6.0
MAX_RODADAS = 3
GRAVIDADES = ("critica", "maior", "menor")

# Critérios (0–10) que cada parecer deve pontuar, por etapa.
CRITERIOS = {
    "01-investigacao": ["delimitacao", "epidemiologia_com_fontes", "pergunta_estruturada",
                        "desfechos_relevantes", "estrategia_de_busca"],
    "03a-busca": ["cobertura_de_bases", "fidelidade_as_strings", "aderencia_aos_criterios",
                  "registro_prisma"],
    "03-evidencias": ["hierarquia_da_evidencia", "extracao_de_dados", "avaliacao_critica",
                      "certeza_grade", "atualidade_das_diretrizes"],
    "02-analise": ["cadeia_causal", "precisao_dos_detalhes", "classificacao_da_certeza",
                   "analise_critica", "qualidade_das_fontes"],
    "04-prescricao": ["seguranca_clinica", "fundamentacao_em_evidencia", "completude_fitt_vp",
                      "criterios_de_progressao", "ajuste_por_sintomas", "especificidade_ao_caso"],
    "artigo-forma": ["estrutura_abnt", "redacao_cientifica", "coesao_do_argumento",
                     "discussao_critica", "ausencia_de_redundancia"],
    "artigo-fidelidade": ["fidelidade_das_citacoes", "precisao_numerica",
                          "ausencia_de_extrapolacao", "coerencia_com_as_etapas"],
    "slides": ["clareza", "ausencia_de_redundancia", "identidade_visual_fps",
               "fidelidade_ao_artigo", "notas_do_apresentador"],
    "banca": ["rigor_cientifico", "qualidade_da_evidencia", "redacao_e_abnt",
              "apresentacao", "coerencia_global", "rigor_das_revisoes"],
}
ORDEM_ETAPAS = list(CRITERIOS)
ETAPAS_ARTIGO = ("artigo-forma", "artigo-fidelidade")


def tipo_trabalho(pasta: Path) -> str:
    """'caso_clinico' ou 'revisao' (padrão), lido do 00-briefing.md."""
    b = pasta / "00-briefing.md"
    if b.exists() and re.search(r"tipo de trabalho:?\**\s*`?caso_clinico", b.read_text(encoding="utf-8"), re.I):
        return "caso_clinico"
    return "revisao"


def etapas_exigidas(pasta: Path) -> list[str]:
    if tipo_trabalho(pasta) == "caso_clinico":
        com_artigo = (pasta / "artigo.json").exists()
        return [e for e in ORDEM_ETAPAS if com_artigo or e not in ETAPAS_ARTIGO]
    return [e for e in ORDEM_ETAPAS if e != "04-prescricao"]


def avaliar_rubrica(par: dict, arq_parecer: Path | None) -> tuple[float | None, list[str]]:
    """Nota estimada pela rubrica do professor (rubrica.json na pasta do trabalho)."""
    itens = par.get("rubrica")
    if not itens:
        return None, []
    avisos = []
    oficial = None
    if arq_parecer is not None:
        r = arq_parecer.resolve().parent.parent / "rubrica.json"
        if r.exists():
            oficial = {c["id"]: c for c in json.loads(r.read_text(encoding="utf-8"))}
    total = 0.0
    for it in itens:
        peso = float(it.get("peso", 0))
        if oficial and it.get("id") in oficial:
            peso = float(oficial[it["id"]]["peso"])
        nota = it.get("nota")
        if not isinstance(nota, (int, float)) or not 0 <= nota <= peso:
            raise ParecerInvalido(f"rubrica {it.get('id')}: nota {nota!r} fora de 0–{peso}")
        if not it.get("justificativa"):
            avisos.append(f"rubrica {it.get('id')}: sem justificativa")
        total += nota
    if oficial:
        faltam = sorted(set(oficial) - {it.get("id") for it in itens})
        if faltam:
            raise ParecerInvalido(f"rubrica sem nota para: {', '.join(faltam)}")
    return round(total, 2), avisos


class ParecerInvalido(ValueError):
    pass


# ------------------------------------------------------------------ util
def _ler(p: Path) -> dict:
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ParecerInvalido(f"{p}: JSON inválido ({e})")


def _norm(s: str) -> str:
    import unicodedata
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


# ------------------------------------------------------------------ modelo
def modelo(etapa: str) -> dict:
    if etapa not in CRITERIOS:
        raise ParecerInvalido(f"etapa desconhecida: {etapa} (use: {', '.join(CRITERIOS)})")
    return {
        "etapa": etapa,
        "rodada": 1,
        "revisor": "fps-lider-…",
        "modelo_revisor": "opus",
        "executor": "fps-…",
        "arquivos_revisados": [],
        "criterios": {c: None for c in CRITERIOS[etapa]},
        "achados": [{
            "id": "A1", "gravidade": "critica|maior|menor", "local": "arquivo > seção",
            "problema": "", "evidencia": "o que foi conferido e onde (PMID, página, trecho)",
            "correcao": "o que exatamente deve ser feito", "responsavel": "fps-…",
            "licao": "regra geral para evitar o erro em qualquer tema (opcional)"}],
        "correcoes_aplicadas": [],
        "pontos_fortes": [],
        "escalonado": False,
        "resumo": "",
    }


# ------------------------------------------------------------------ avaliar
def avaliar(par: dict, arq: Path | None = None) -> tuple[str, list[str], dict]:
    """Retorna (decisão, avisos, estatísticas)."""
    avisos: list[str] = []
    etapa = par.get("etapa")
    if etapa not in CRITERIOS:
        raise ParecerInvalido(f"etapa desconhecida: {etapa}")
    for campo in ("rodada", "revisor", "criterios", "achados", "resumo"):
        if campo not in par:
            raise ParecerInvalido(f"campo obrigatório ausente: {campo}")
    notas = par["criterios"]
    faltando = [c for c in CRITERIOS[etapa] if notas.get(c) is None]
    if faltando:
        raise ParecerInvalido(f"critérios sem nota: {', '.join(faltando)}")
    extras = [c for c in notas if c not in CRITERIOS[etapa]]
    if extras:
        avisos.append(f"critérios extras ignorados no portão: {', '.join(extras)}")
    valores = []
    for c in CRITERIOS[etapa]:
        v = notas[c]
        if not isinstance(v, (int, float)) or not 0 <= v <= 10:
            raise ParecerInvalido(f"nota inválida em '{c}': {v!r} (0–10)")
        valores.append(float(v))
    ids = set()
    cont = {g: 0 for g in GRAVIDADES}
    for a in par["achados"]:
        for campo in ("id", "gravidade", "local", "problema", "correcao", "responsavel"):
            if not a.get(campo):
                raise ParecerInvalido(f"achado {a.get('id', '?')} sem '{campo}'")
        if a["gravidade"] not in GRAVIDADES:
            raise ParecerInvalido(f"achado {a['id']}: gravidade '{a['gravidade']}' inválida")
        if a["id"] in ids:
            raise ParecerInvalido(f"id de achado repetido: {a['id']}")
        ids.add(a["id"])
        cont[a["gravidade"]] += 1
        if a["gravidade"] in ("critica", "maior") and not a.get("evidencia"):
            avisos.append(f"achado {a['id']} ({a['gravidade']}) sem 'evidencia' — o executor precisa saber o que foi conferido")
    media = sum(valores) / len(valores)
    minimo = min(valores)
    aprovado = cont["critica"] == 0 and cont["maior"] == 0 and media >= MEDIA_MINIMA and minimo >= NOTA_MINIMA
    if aprovado:
        decisao = "APROVADO"
    elif par.get("escalonado"):
        decisao = "ESCALAR"  # o revisor já assumiu a correção; precisa resolver e reavaliar
    elif int(par["rodada"]) >= MAX_RODADAS:
        decisao = "ESCALAR"
    else:
        decisao = "REVISAR"
    vr = par.get("veredito_revisor")
    if vr and vr != decisao:
        avisos.append(f"veredito do revisor ({vr}) difere do portão ({decisao}); vale o portão")
    if aprovado and cont["menor"]:
        avisos.append(f"{cont['menor']} achado(s) menor(es): o revisor deve corrigir direto e registrar em 'correcoes_aplicadas'")
    if not aprovado and media >= MEDIA_MINIMA and not (cont["critica"] or cont["maior"]):
        avisos.append(f"reprovado por nota mínima < {NOTA_MINIMA}")
    est = {"media": round(media, 2), "minimo": minimo, **cont}
    nota_rubrica, av_rub = avaliar_rubrica(par, arq)
    avisos += av_rub
    if nota_rubrica is not None:
        est["nota_rubrica"] = nota_rubrica
    return decisao, avisos, est


# ------------------------------------------------------------------ resposta
def conferir_resposta(resp: dict | list, par: dict) -> list[str]:
    itens = resp.get("itens", resp) if isinstance(resp, dict) else resp
    por_id = {i.get("id"): i for i in itens}
    problemas = []
    for a in par["achados"]:
        if a["gravidade"] == "menor":
            continue
        r = por_id.get(a["id"])
        if r is None:
            problemas.append(f"achado {a['id']} ({a['gravidade']}) sem resposta")
        elif r.get("status") not in ("corrigido", "contestado"):
            problemas.append(f"achado {a['id']}: status '{r.get('status')}' (use corrigido|contestado)")
        elif not r.get("detalhe"):
            problemas.append(f"achado {a['id']}: sem 'detalhe' (o que mudou ou por que contesta)")
        elif r["status"] == "contestado" and len(r["detalhe"]) < 40:
            problemas.append(f"achado {a['id']}: contestação sem justificativa suficiente")
    return problemas


# ------------------------------------------------------------------ painel
RE_ARQ = re.compile(r"^(?P<etapa>[\w-]+)\.r(?P<rodada>\d+)\.parecer\.json$")


def pareceres(pasta: Path) -> dict[str, list[tuple[int, Path]]]:
    out: dict[str, list[tuple[int, Path]]] = {}
    for p in sorted((pasta / "revisoes").glob("*.parecer.json")):
        m = RE_ARQ.match(p.name)
        if m:
            out.setdefault(m["etapa"], []).append((int(m["rodada"]), p))
    for v in out.values():
        v.sort()
    return out


def painel(pasta: Path) -> str:
    linhas = [f"# Painel de qualidade — {pasta.name}", "",
              f"Atualizado em {dt.datetime.now():%d/%m/%Y %H:%M}.", "",
              "| Etapa | Executor | Revisor (modelo) | Rodadas | Decisão | Crít. | Maior | Menor | Média |",
              "|---|---|---|---|---|---|---|---|---|"]
    todos = pareceres(pasta)
    linhas.insert(2, f"Tipo de trabalho: `{tipo_trabalho(pasta)}`.")
    linhas.insert(3, "")
    for etapa in etapas_exigidas(pasta):
        if etapa not in todos:
            linhas.append(f"| {etapa} | — | — | 0 | pendente | | | | |")
            continue
        rod, arq = todos[etapa][-1]
        try:
            par = _ler(arq)
            dec, _, est = avaliar(par, arq)
        except ParecerInvalido as e:
            linhas.append(f"| {etapa} | ? | ? | {rod} | INVÁLIDO: {e} | | | | |")
            continue
        if "nota_rubrica" in est:
            nota_banca = est["nota_rubrica"]
        linhas.append(f"| {etapa} | {par.get('executor', '?')} | {par.get('revisor', '?')} "
                      f"({par.get('modelo_revisor', '?')}) | {rod} | **{dec}** | {est['critica']} | "
                      f"{est['maior']} | {est['menor']} | {est['media']:.1f} |")
    if "nota_banca" in locals():
        linhas += ["", f"**Nota estimada pela banca (rubrica do professor): {nota_banca:.1f} / 10**"]
    linhas += ["", "Portão: aprova com 0 críticos, 0 maiores, média ≥ 7,5 e nenhuma nota < 6. "
               "3ª rodada sem aprovação → ESCALAR (o revisor corrige diretamente)."]
    return "\n".join(linhas) + "\n"


# ------------------------------------------------------------------ lições
def _carregar_memoria() -> dict:
    arq = MEMORIA / "licoes.json"
    if arq.exists():
        return json.loads(arq.read_text(encoding="utf-8"))
    return {"agentes": {}}


def _render_memoria(mem: dict) -> str:
    linhas = ["# Memória de lições do pipeline FPS", "",
              "Gerado por `scripts/parecer.py licoes` a partir dos pareceres dos revisores.",
              "Cada executor lê a sua seção **antes** de começar. Não edite à mão: edite `licoes.json`.", ""]
    for agente in sorted(mem["agentes"]):
        itens = sorted(mem["agentes"][agente], key=lambda x: (-x["ocorrencias"], x["texto"]))
        if not itens:
            continue
        linhas.append(f"## {agente}")
        for it in itens:
            linhas.append(f"- {it['texto']} *(visto {it['ocorrencias']}x; último: {it['ultimo']})*")
        linhas.append("")
    return "\n".join(linhas)


def licoes(pasta: Path, limite_por_agente: int = 12) -> tuple[int, int]:
    mem = _carregar_memoria()
    novas = reforcadas = 0
    hoje = dt.date.today().isoformat()
    for etapa, lst in pareceres(pasta).items():
        for _, arq in lst:
            par = _ler(arq)
            for a in par.get("achados", []):
                txt = (a.get("licao") or "").strip()
                if len(txt) < 15:
                    continue
                agente = a.get("responsavel", "geral")
                bucket = mem["agentes"].setdefault(agente, [])
                alvo = next((b for b in bucket
                             if difflib.SequenceMatcher(None, _norm(b["texto"]), _norm(txt)).ratio() > 0.8), None)
                chave = f"{pasta.name}:{arq.name}:{a['id']}"
                if alvo:
                    if chave not in alvo.setdefault("origens", []):
                        alvo["ocorrencias"] += 1
                        alvo["ultimo"] = hoje
                        alvo["origens"].append(chave)
                        reforcadas += 1
                else:
                    bucket.append({"texto": txt, "ocorrencias": 1, "ultimo": hoje, "origens": [chave]})
                    novas += 1
    for agente, bucket in mem["agentes"].items():
        bucket.sort(key=lambda x: x["ultimo"], reverse=True)   # mais recentes primeiro…
        bucket.sort(key=lambda x: -x["ocorrencias"])           # …dentro de mais frequentes
        del bucket[limite_por_agente:]
    MEMORIA.mkdir(exist_ok=True)
    (MEMORIA / "licoes.json").write_text(json.dumps(mem, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (MEMORIA / "licoes.md").write_text(_render_memoria(mem), encoding="utf-8")
    return novas, reforcadas


# ------------------------------------------------------------------ CLI
def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, alvo = argv[1], argv[2]
    try:
        if cmd == "modelo":
            print(json.dumps(modelo(alvo), ensure_ascii=False, indent=2))
            return 0
        if cmd == "avaliar":
            par = _ler(Path(alvo))
            dec, avisos, est = avaliar(par, Path(alvo))
            print(f"{par['etapa']} · rodada {par['rodada']} · {dec}")
            if "nota_rubrica" in est:
                print(f"  nota estimada pela rubrica do professor: {est['nota_rubrica']:.1f} / 10")
            print(f"  média {est['media']:.2f} · mínimo {est['minimo']:.1f} · "
                  f"críticos {est['critica']} · maiores {est['maior']} · menores {est['menor']}")
            for a in avisos:
                print(f"  aviso: {a}")
            pend = [a for a in par["achados"] if a["gravidade"] != "menor"]
            if dec != "APROVADO" and pend:
                print("  pendências para o executor:")
                for a in pend:
                    print(f"   - [{a['id']}·{a['gravidade']}] {a['responsavel']}: {a['problema'][:110]}")
            return {"APROVADO": 0, "REVISAR": 1, "ESCALAR": 3}[dec]
        if cmd == "resposta":
            probs = conferir_resposta(_ler(Path(alvo)), _ler(Path(argv[3])))
            for p in probs:
                print(f"  problema: {p}")
            print("resposta completa" if not probs else f"{len(probs)} problema(s) na resposta")
            return 1 if probs else 0
        if cmd == "painel":
            pasta = Path(alvo)
            txt = painel(pasta)
            (pasta / "painel.md").write_text(txt, encoding="utf-8")
            print(txt)
            return 0
        if cmd == "licoes":
            n, r = licoes(Path(alvo))
            print(f"{n} lição(ões) nova(s), {r} reforçada(s) → {MEMORIA / 'licoes.md'}")
            return 0
    except ParecerInvalido as e:
        print(f"PARECER INVÁLIDO: {e}", file=sys.stderr)
        return 2
    print(f"comando desconhecido: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
