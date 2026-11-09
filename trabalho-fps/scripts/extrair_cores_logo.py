#!/usr/bin/env python3
"""Extrai a paleta da marca a partir do logo oficial da FPS e (opcionalmente)
grava em marca/marca-fps.json e gera a versão branca do logo para fundos escuros.

Uso:
  python3 extrair_cores_logo.py marca/logo-fps.png            # só mostra a paleta
  python3 extrair_cores_logo.py marca/logo-fps.png --salvar   # grava marca-fps.json
  python3 extrair_cores_logo.py marca/logo-fps.png --salvar --gerar-negativo

Regras: ignora fundo branco/transparente e tons de cinza; garante contraste
WCAG >= 4.5 da cor primária com o branco (títulos e fundos de capa).
"""
from __future__ import annotations

import argparse
import colorsys
import json
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent


def lum(rgb):
    def c(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def hexa(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def escurecer(rgb, alvo=4.5):
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
    while contraste(tuple(int(v * 255) for v in colorsys.hls_to_rgb(h, l, s)), (255, 255, 255)) < alvo and l > 0.05:
        l -= 0.02
    return tuple(int(round(v * 255)) for v in colorsys.hls_to_rgb(h, l, s))


def clarear(rgb, fator=0.94):
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
    return tuple(int(round(v * 255)) for v in colorsys.hls_to_rgb(h, fator, min(s, 0.35)))


def com_transparencia(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    borda = [px[x, 0] for x in range(w)] + [px[x, h - 1] for x in range(w)] + \
            [px[0, y] for y in range(h)] + [px[w - 1, y] for y in range(h)]
    fundo_branco = sum(1 for p in borda if p[3] > 0 and min(p[:3]) > 235) > 0.8 * len(borda)
    if fundo_branco:
        for y in range(h):
            for x in range(w):
                r, g, b, a = px[x, y]
                if min(r, g, b) > 235:
                    px[x, y] = (r, g, b, 0)
    return img


def paleta(img: Image.Image, n=3):
    rgba = img.convert("RGBA")
    rgba.thumbnail((300, 300))
    dados = rgba.get_flattened_data() if hasattr(rgba, "get_flattened_data") else rgba.getdata()
    pixels = [p[:3] for p in dados if p[3] > 200]
    if not pixels:
        sys.exit("Logo sem pixels opacos.")
    amostra = Image.new("RGB", (len(pixels), 1))
    amostra.putdata(pixels)
    q = amostra.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    contagem = sorted(q.getcolors(), reverse=True)
    cores = []
    for qtd, idx in contagem:
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
        if s < 0.18 or l > 0.92 or l < 0.06:  # cinzas, branco e preto
            continue
        if any(abs(h - colorsys.rgb_to_hls(*(v / 255 for v in c))[0]) < 0.04 for c, _ in cores):
            continue
        cores.append((rgb, qtd))
    return [c for c, _ in cores[:n]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logo", type=Path)
    ap.add_argument("--salvar", action="store_true", help="grava as cores em marca/marca-fps.json")
    ap.add_argument("--gerar-negativo", action="store_true", help="gera marca/logo-fps-branco.png")
    ap.add_argument("--marca", type=Path, default=RAIZ / "marca" / "marca-fps.json")
    a = ap.parse_args()

    img = com_transparencia(Image.open(a.logo))
    cores = paleta(img)
    if not cores:
        sys.exit("Nenhuma cor de marca encontrada (logo monocromático?). Defina as cores manualmente.")
    # A mais escura das duas mais frequentes vira primária (títulos e fundos).
    principais = sorted(cores[:2], key=lum)
    primaria = principais[0]
    secundaria = principais[1] if len(principais) > 1 else cores[0]
    destaque = cores[2] if len(cores) > 2 else None
    primaria_ok = primaria if contraste(primaria, (255, 255, 255)) >= 4.5 else escurecer(primaria)
    secundaria_ok = secundaria if contraste(secundaria, (255, 255, 255)) >= 3 else escurecer(secundaria, 3)

    novas = {
        "primaria": hexa(primaria_ok),
        "secundaria": hexa(secundaria_ok),
        "fundo_suave": hexa(clarear(primaria)),
    }
    if destaque:
        novas["destaque"] = hexa(destaque)
    print("Cores encontradas no logo:", ", ".join(hexa(c) for c in cores))
    for k, v in novas.items():
        print(f"  {k:12s} {v}")
    if primaria_ok != primaria:
        print(f"  (primária escurecida de {hexa(primaria)} para garantir contraste com texto branco)")

    if a.salvar:
        dados = json.loads(a.marca.read_text(encoding="utf-8"))
        dados["cores"].update(novas)
        dados.pop("_status", None)
        dados["logo"] = a.logo.name if a.logo.resolve().parent == a.marca.resolve().parent else str(a.logo)
        a.marca.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Paleta gravada em {a.marca}")
    if a.gerar_negativo:
        branco = Image.new("RGBA", img.size, (255, 255, 255, 0))
        alfa = img.getchannel("A")
        branco.paste((255, 255, 255, 255), mask=alfa)
        destino = a.marca.parent / "logo-fps-branco.png"
        branco.save(destino)
        print(f"Logo negativo (branco) gerado: {destino}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
