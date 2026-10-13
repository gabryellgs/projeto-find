"""Avalia as páginas da amostra com o axe-core.

Uso (com o servidor rodando em outro terminal):
    python acessibilidade/avaliar_axe.py --rotulo antes
"""
import argparse
import csv
import json
import platform
from datetime import datetime
from importlib import metadata
from pathlib import Path

from axe_playwright_python.sync_playwright import Axe
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SENHA = "Avaliacao@2026"
USUARIO = "avaliadora@example.com"
USUARIO_POR_PAGINA = {"P13": "visitante@example.com"}
TAGS_WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"]
VIEWPORT = {"width": 1366, "height": 768}
CANAL = "msedge"  # ou "chrome"
PASTA = Path(__file__).parent


def ler_paginas():
    with open(PASTA / "paginas.csv", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def fazer_login(page, usuario):
    page.goto(f"{BASE_URL}/login/")
    page.fill('input[name="username"]', usuario)
    page.fill('input[name="password"]', SENHA)
    with page.expect_navigation():
        page.click("#btn-submit")


def criterios_wcag(tags):
    # converte tags como 'wcag143' em '1.4.3'
    return [".".join(t[4:]) for t in tags if t.startswith("wcag") and t[4:].isdigit()]


def gravar_execucao(destino, rotulo, axe_core, navegador):
    dados = {
        "rotulo": rotulo,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "sistema": platform.platform(),
        "python": platform.python_version(),
        "django": metadata.version("django"),
        "playwright": metadata.version("playwright"),
        "axe-playwright-python": metadata.version("axe-playwright-python"),
        "axe-core": axe_core,
        "navegador": navegador,
        "resolucao": f"{VIEWPORT['width']}x{VIEWPORT['height']}",
        "tags": " ".join(TAGS_WCAG),
    }
    texto = "\n".join(f"{chave}: {valor}" for chave, valor in dados.items())
    (destino / "execucao.txt").write_text(texto + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotulo", required=True, help="antes ou depois")
    args = parser.parse_args()

    destino = PASTA / "resultados" / args.rotulo
    destino.mkdir(parents=True, exist_ok=True)
    axe = Axe()
    linhas = []

    with sync_playwright() as p:
        navegador = p.chromium.launch(channel=CANAL)
        for pagina in ler_paginas():
            # um contexto novo por página, para todas começarem do mesmo estado
            contexto = navegador.new_context(bypass_csp=True, viewport=VIEWPORT)
            page = contexto.new_page()
            if pagina["requer_login"] == "sim":
                fazer_login(page, USUARIO_POR_PAGINA.get(pagina["id"], USUARIO))
            page.goto(BASE_URL + pagina["url"], wait_until="load")
            page.wait_for_timeout(1500)

            resultado = axe.run(page, options={"runOnly": {"type": "tag", "values": TAGS_WCAG}})
            dados = resultado.response
            (destino / f"{pagina['id']}.json").write_text(
                json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            for violacao in dados["violations"]:
                linhas.append({
                    "pagina": pagina["id"],
                    "regra": violacao["id"],
                    "impacto": violacao["impact"],
                    "criterios": " ".join(criterios_wcag(violacao["tags"])),
                    "ocorrencias": len(violacao["nodes"]),
                    "descricao": violacao["help"],
                })
            print(f"{pagina['id']}: {len(dados['violations'])} regras violadas")
            contexto.close()
        versao_navegador = f"{CANAL} (Chromium {navegador.version})"
        navegador.close()

    campos = ["pagina", "regra", "impacto", "criterios", "ocorrencias", "descricao"]
    with open(destino / "resumo.csv", "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(linhas)

    axe_core = dados["testEngine"]["version"]
    gravar_execucao(destino, args.rotulo, axe_core, versao_navegador)
    print(f"Versão do axe-core: {axe_core}")


if __name__ == "__main__":
    main()
