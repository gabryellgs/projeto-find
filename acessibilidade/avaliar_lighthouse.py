"""Roda o Lighthouse (só Acessibilidade, preset desktop) nas páginas da amostra.

Uso (com o servidor rodando em outro terminal):
    python acessibilidade/avaliar_lighthouse.py --rotulo antes
"""
import argparse
import csv
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"
SENHA = "Avaliacao@2026"
USUARIO = "avaliadora@example.com"
VERSAO_LIGHTHOUSE = "13.4.1"
CANAL = "msedge"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PASTA = Path(__file__).parent


def ler_paginas():
    with open(PASTA / "paginas.csv", encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def fazer_login(page):
    page.goto(f"{BASE_URL}/login/")
    page.fill('input[name="username"]', USUARIO)
    page.fill('input[name="password"]', SENHA)
    with page.expect_navigation():
        page.click("#btn-submit")


def cookie_de_sessao(p):
    navegador = p.chromium.launch(channel=CANAL)
    versao = navegador.version
    contexto = navegador.new_context()
    fazer_login(contexto.new_page())
    cookies = "; ".join(f"{c['name']}={c['value']}" for c in contexto.cookies())
    navegador.close()
    return cookies, versao


def rodar_lighthouse(url, saida, cookies=None):
    # o Lighthouse abre o próprio Edge, com perfil novo e sem extensões
    comando = [
        shutil.which("npx"), "--yes", f"lighthouse@{VERSAO_LIGHTHOUSE}", url,
        "--preset=desktop", "--only-categories=accessibility",
        "--output=html", "--output=json", f"--output-path={saida}",
        "--chrome-flags=--headless=new", "--quiet",
    ]
    if cookies:
        comando.append(f'--extra-headers={json.dumps({"Cookie": cookies})}')
    subprocess.run(comando, check=True, env={**os.environ, "CHROME_PATH": EDGE})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rotulo", required=True, help="antes ou depois")
    args = parser.parse_args()

    destino = PASTA / "resultados" / args.rotulo / "lighthouse"
    destino.mkdir(parents=True, exist_ok=True)
    linhas = []

    with sync_playwright() as p:
        cookies, versao_navegador = cookie_de_sessao(p)

    for pagina in ler_paginas():
        saida = destino / pagina["id"]
        sessao = cookies if pagina["requer_login"] == "sim" else None
        rodar_lighthouse(BASE_URL + pagina["url"], saida, sessao)

        relatorio = json.loads((destino / f"{pagina['id']}.report.json").read_text(encoding="utf-8"))
        final = relatorio["finalDisplayedUrl"]
        if not final.rstrip("/").endswith(pagina["url"].rstrip("/")):
            print(f"Atenção: {pagina['id']} terminou em {final}")
        nota = round(relatorio["categories"]["accessibility"]["score"] * 100)
        reprovadas = [
            nome for nome, auditoria in relatorio["audits"].items()
            if auditoria["score"] == 0 and auditoria.get("scoreDisplayMode") == "binary"
        ]
        linhas.append({"pagina": pagina["id"], "pontuacao": nota, "auditorias_reprovadas": " ".join(reprovadas)})
        print(f"{pagina['id']}: {nota}")

    with open(destino / "resumo.csv", "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["pagina", "pontuacao", "auditorias_reprovadas"])
        escritor.writeheader()
        escritor.writerows(linhas)

    texto = (
        f"rotulo: {args.rotulo}\n"
        f"data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"lighthouse: {relatorio['lighthouseVersion']}\n"
        f"navegador: {CANAL} (Chromium {versao_navegador})\n"
        f"configuracao: modo navegacao, preset desktop, categoria accessibility\n"
    )
    (destino / "execucao.txt").write_text(texto, encoding="utf-8")


if __name__ == "__main__":
    main()
