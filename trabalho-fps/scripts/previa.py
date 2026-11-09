#!/usr/bin/env python3
"""Renderiza .docx/.pptx em PNG (via LibreOffice + pdftoppm) para revisão visual.

Uso:
  python3 previa.py arquivo.docx|arquivo.pptx [-o pasta] [--dpi 70]

Gera <pasta>/pagina-01.png, ... e <pasta>/folha-de-contato.png (todas as páginas
num único painel). Os subagentes usam essas imagens para conferir layout,
quebras, sobreposições e texto estourando antes de entregar.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def renderizar(arquivo: Path, pasta: Path, dpi: int = 70) -> list[Path]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("LibreOffice (soffice) não encontrado; instale para gerar a prévia.")
    if not shutil.which("pdftoppm"):
        sys.exit("pdftoppm (poppler-utils) não encontrado.")
    pasta.mkdir(parents=True, exist_ok=True)
    for velho in pasta.glob("pagina-*.png"):
        velho.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        perfil = Path(tmp) / "perfil"
        subprocess.run([soffice, f"-env:UserInstallation=file://{perfil}", "--headless",
                        "--convert-to", "pdf", "--outdir", tmp, str(arquivo)],
                       check=True, capture_output=True, timeout=240)
        pdf = Path(tmp) / (arquivo.stem + ".pdf")
        if not pdf.exists():
            sys.exit("Falha na conversão para PDF.")
        shutil.copy(pdf, pasta / (arquivo.stem + ".pdf"))
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), str(pdf), str(pasta / "pagina")],
                       check=True, timeout=240)
    paginas = sorted(pasta.glob("pagina-*.png"))
    # pdftoppm numera com zeros variáveis; normaliza para pagina-01.png
    norm = []
    for i, p in enumerate(paginas, start=1):
        alvo = pasta / f"pagina-{i:02d}.png"
        if p != alvo:
            p.rename(alvo)
        norm.append(alvo)
    return norm


def folha_contato(paginas: list[Path], destino: Path, colunas: int = 4) -> Path | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    if not paginas:
        return None
    imgs = [Image.open(p).convert("RGB") for p in paginas]
    w = max(i.width for i in imgs)
    h = max(i.height for i in imgs)
    escala = min(1.0, 480 / w)
    tw, th = int(w * escala), int(h * escala)
    linhas = (len(imgs) + colunas - 1) // colunas
    margem = 12
    painel = Image.new("RGB", (colunas * (tw + margem) + margem, linhas * (th + margem) + margem), "#D0D5DB")
    for k, im in enumerate(imgs):
        im = im.resize((tw, int(im.height * escala)))
        x = margem + (k % colunas) * (tw + margem)
        y = margem + (k // colunas) * (th + margem)
        painel.paste(im, (x, y))
    painel.save(destino)
    return destino


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", type=Path)
    ap.add_argument("-o", "--pasta", type=Path)
    ap.add_argument("--dpi", type=int, default=70)
    a = ap.parse_args()
    pasta = a.pasta or a.arquivo.parent / f"previa-{a.arquivo.stem}"
    paginas = renderizar(a.arquivo.resolve(), pasta, a.dpi)
    contato = folha_contato(paginas, pasta / "folha-de-contato.png",
                            colunas=3 if a.arquivo.suffix == ".pptx" else 4)
    print(f"{len(paginas)} página(s) em {pasta}")
    if contato:
        print(f"folha de contato: {contato}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
