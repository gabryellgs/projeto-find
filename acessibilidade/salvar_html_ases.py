"""Salva o código-fonte das páginas com login para avaliar no ASES Web.

Uso (com o servidor rodando em outro terminal):
    python acessibilidade/salvar_html_ases.py --rotulo antes
"""
import argparse
import csv
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SENHA = "Avaliacao@2026"
USUARIO = "avaliadora@example.com"
CANAL = "msedge"
PASTA = Path(__file__).parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotulo", required=True, help="antes ou depois")
    args = parser.parse_args()

    destino = PASTA / "resultados" / args.rotulo / "ases"
    destino.mkdir(parents=True, exist_ok=True)
    with open(PASTA / "paginas.csv", encoding="utf-8") as arquivo:
        paginas = [p for p in csv.DictReader(arquivo) if p["requer_login"] == "sim"]

    with sync_playwright() as p:
        navegador = p.chromium.launch(channel=CANAL)
        page = navegador.new_context().new_page()
        page.goto(f"{BASE_URL}/login/")
        page.fill('input[name="username"]', USUARIO)
        page.fill('input[name="password"]', SENHA)
        with page.expect_navigation():
            page.click("#btn-submit")

        for pagina in paginas:
            resposta = page.goto(BASE_URL + pagina["url"], wait_until="load")
            # texto da resposta do servidor, o mesmo que o "exibir código-fonte" mostra
            (destino / f"{pagina['id']}.html").write_text(resposta.text(), encoding="utf-8")
            print(f"{pagina['id']}: {resposta.status}")
        navegador.close()


if __name__ == "__main__":
    main()
