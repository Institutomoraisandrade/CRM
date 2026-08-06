"""Conversão do relatório HTML em PDF.

Usa o Chrome/Chromium em modo headless, que praticamente toda máquina já
tem instalado. Evita uma dependência pesada de geração de PDF só para
imprimir uma página que já existe em HTML.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

# Nomes e caminhos onde o Chrome costuma estar, por sistema.
CANDIDATOS = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)

AJUDA = (
    "Não encontrei o Chrome nem o Chromium para gerar o PDF.\n"
    "Instale um dos dois, ou aponte o caminho na variável de ambiente "
    "AGENTE_CHROME.\n"
    "O relatório em HTML continua sendo gerado normalmente."
)


class ErroDePDF(Exception):
    """Falha ao converter o relatório em PDF."""


def encontrar_chrome() -> str | None:
    """Localiza um executável do Chrome/Chromium utilizável."""
    indicado = os.environ.get("AGENTE_CHROME")
    if indicado and Path(indicado).exists():
        return indicado

    for candidato in CANDIDATOS:
        caminho = shutil.which(candidato)
        if caminho:
            return caminho
        if Path(candidato).exists():
            return candidato

    # Instalações do Playwright, comuns em quem já usa automação.
    for base in (Path.home() / ".cache/ms-playwright", Path("/opt/pw-browsers")):
        if base.is_dir():
            for achado in sorted(base.glob("chromium-*/chrome-linux/chrome")):
                return str(achado)
            for achado in sorted(base.glob("chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium")):
                return str(achado)
    return None


def html_para_pdf(html: str, destino: str | Path, titulo: str = "") -> Path:
    """Escreve o HTML como PDF em ``destino``.

    O HTML recebe um cabeçalho de página e margens próprias para
    impressão, já que o relatório foi desenhado para e-mail.
    """
    chrome = encontrar_chrome()
    if chrome is None:
        raise ErroDePDF(AJUDA)

    destino = Path(destino).expanduser()
    destino.parent.mkdir(parents=True, exist_ok=True)

    pagina = _envelopar(html, titulo)
    with tempfile.TemporaryDirectory() as temporario:
        origem = Path(temporario) / "relatorio.html"
        origem.write_text(pagina, encoding="utf-8")
        comando = [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={destino}",
            origem.as_uri(),
        ]
        try:
            processo = subprocess.run(
                comando, capture_output=True, timeout=120, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as erro:
            raise ErroDePDF(f"falha ao executar {chrome}: {erro}") from erro

    if not destino.exists() or destino.stat().st_size == 0:
        detalhe = (processo.stderr or b"").decode("utf-8", "replace")[-400:]
        raise ErroDePDF(f"o Chrome não gerou o PDF. Saída:\n{detalhe}")
    return destino


def _envelopar(html: str, titulo: str) -> str:
    """Acrescenta o esqueleto de página e o estilo de impressão."""
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<title>{titulo or 'Relatório de agendamento'}</title>
<style>
  @page {{ size: A4; margin: 14mm 12mm; }}
  body {{ margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  table {{ page-break-inside: auto; }}
  tr {{ page-break-inside: avoid; page-break-after: auto; }}
  thead {{ display: table-header-group; }}
  h2, h3 {{ page-break-after: avoid; }}
</style></head>
<body>{html}</body></html>"""
