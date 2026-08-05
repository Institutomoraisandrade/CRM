"""Descobre como o LiveClin serve os dados, sem expor dado de paciente.

Roda **na sua máquina**. Abre um navegador comum, espera você fazer login
e navegar até a tela de pacientes, e anota quais chamadas de API o site
faz por baixo. Grava só o *formato* das respostas — nomes de campos e
tipos — nunca o conteúdo.

O resultado é um arquivo que pode ser enviado ao desenvolvedor para
escrever o leitor definitivo, no lugar de exportar planilha toda vez.

Uso:

    pip install playwright && playwright install chromium
    python3 ferramentas/capturar_liveclin.py

O login acontece na janela do navegador, como sempre. A senha não passa
por este script nem fica gravada em lugar nenhum: o Playwright guarda
apenas o cookie de sessão, na pasta ``.perfil_liveclin`` local.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ENDERECO_PADRAO = "https://v2.liveclin.com/inbox"
PERFIL = Path(".perfil_liveclin")
SAIDA = Path("captura_liveclin.json")

# Campos cujo valor nunca deve ser gravado, nem como amostra.
SENSIVEIS = {
    "nome", "name", "nome_completo", "fullname", "email", "e-mail",
    "telefone", "phone", "whatsapp", "celular", "cpf", "documento",
    "document", "birthdate", "data_nascimento", "endereco", "address",
    "token", "authorization", "password", "senha", "access_token",
}

# Campos categóricos: o valor é uma classificação, não uma pessoa. São
# exatamente o que precisa ser mapeado ("Ativos - Daniel", "Semestral"),
# então o texto é preservado.
CATEGORICOS = {
    "plano", "plan", "planos", "servico", "modalidade",
    "etiqueta", "etiquetas", "tag", "tags", "label", "labels",
    "status", "situacao", "tipo", "type",
}


def formato(valor, profundidade: int = 0, dentro_de: str | None = None):
    """Descreve a estrutura de um JSON sem revelar o conteúdo.

    Guarda nomes de campos e tipos. Valores viram o nome do tipo, com duas
    exceções deliberadas: campos categóricos (plano, etiqueta, status)
    mostram o texto real, porque são o que precisa ser mapeado e não
    identificam ninguém.
    """
    if profundidade > 6:
        return "..."
    if isinstance(valor, dict):
        saida = {}
        for chave, v in list(valor.items())[:40]:
            baixa = chave.lower()
            if baixa in SENSIVEIS and dentro_de not in CATEGORICOS:
                saida[chave] = "<oculto>"
            else:
                # Dentro de um bloco categórico, os filhos seguem
                # categóricos: "plano": {"nome": "Semestral"} é o rótulo
                # do plano, não o nome de uma pessoa.
                contexto = dentro_de if dentro_de in CATEGORICOS else baixa
                saida[chave] = formato(v, profundidade + 1, contexto)
        return saida
    if isinstance(valor, list):
        if not valor:
            return []
        return [formato(valor[0], profundidade + 1, dentro_de), f"...({len(valor)} itens)"]
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return type(valor).__name__
    if valor is None:
        return None
    texto = str(valor)
    # Categorias são o alvo do mapeamento: plano, etiqueta, status.
    if dentro_de in CATEGORICOS and len(texto) <= 60:
        return texto
    # Datas ajudam a identificar o campo e não identificam ninguém.
    if len(texto) <= 10 and any(c in texto for c in "/-") and any(c.isdigit() for c in texto):
        return f"<data? {len(texto)} chars>"
    return f"<str {len(texto)} chars>"


def interessante(url: str) -> bool:
    ignorar = (".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2", ".ico", ".gif")
    if url.endswith(ignorar):
        return False
    return any(p in url for p in ("/api", "/v1", "/v2", "/graphql", "/rest", "json"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endereco", default=ENDERECO_PADRAO)
    parser.add_argument("--saida", default=str(SAIDA))
    parser.add_argument(
        "--segundos", type=int, default=300,
        help="quanto tempo a janela fica aberta para você navegar (padrão: 300)",
    )
    args = parser.parse_args(argv)

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Instale o Playwright primeiro:\n"
            "  pip install playwright\n"
            "  playwright install chromium",
            file=sys.stderr,
        )
        return 1

    chamadas: dict[str, dict] = {}

    def registrar(resposta):
        url = resposta.url
        if not interessante(url):
            return
        chave = f"{resposta.request.method} {url.split('?')[0]}"
        if chave in chamadas:
            chamadas[chave]["vezes"] += 1
            return
        registro = {
            "metodo": resposta.request.method,
            "url": url.split("?")[0],
            "parametros": sorted(
                p.split("=")[0] for p in url.split("?")[1].split("&")
            ) if "?" in url else [],
            "status": resposta.status,
            "vezes": 1,
            "resposta": None,
        }
        try:
            if "json" in (resposta.headers.get("content-type") or ""):
                registro["resposta"] = formato(resposta.json())
        except Exception as erro:  # resposta binária, vazia ou já descartada
            registro["resposta"] = f"<não consegui ler: {type(erro).__name__}>"
        chamadas[chave] = registro

    print("Abrindo o navegador. Faça login e navegue até a lista de pacientes.")
    print("Use os filtros de etiqueta (Ativos - Daniel, Ativos - Juliana) e abra")
    print("a ficha de um paciente, para o script ver todas as chamadas.")
    print(f"A janela fecha sozinha em {args.segundos}s, ou feche você mesmo.\n")

    with sync_playwright() as pw:
        contexto = pw.chromium.launch_persistent_context(
            user_data_dir=str(PERFIL), headless=False, viewport={"width": 1400, "height": 900}
        )
        contexto.on("response", registrar)
        pagina = contexto.pages[0] if contexto.pages else contexto.new_page()
        pagina.goto(args.endereco, wait_until="domcontentloaded")
        try:
            pagina.wait_for_timeout(args.segundos * 1000)
        except Exception:
            pass  # janela fechada pelo usuário
        finally:
            try:
                contexto.close()
            except Exception:
                pass

    destino = Path(args.saida)
    destino.write_text(
        json.dumps(
            {
                "capturado_em": datetime.now().isoformat(timespec="seconds"),
                "endereco": args.endereco,
                "aviso": (
                    "Só o formato das respostas foi gravado. Campos com nome, "
                    "telefone, e-mail e documento aparecem como <oculto>; textos "
                    "viram <str N chars>."
                ),
                "chamadas": sorted(chamadas.values(), key=lambda c: -c["vezes"]),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\n{len(chamadas)} chamada(s) de API registradas em {destino}")
    if not chamadas:
        print(
            "Nenhuma chamada reconhecida. Pode ser que o site use outro padrão de "
            "URL — abra o arquivo e confira, ou rode de novo navegando mais."
        )
        return 1
    print("Confira o arquivo antes de enviar: ele não deve conter nome de paciente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
