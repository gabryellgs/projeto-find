import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from openpyxl import load_workbook

PASTA = Path(__file__).parent
RESULTADOS = PASTA / "resultados"
DESTINO = RESULTADOS / "comparativo"

COR_ANTES = "#2a78d6"
COR_DEPOIS = "#eb6834"
TEXTO = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
GRADE = "#e3e2de"

METRICAS = [
    ("axe: regras violadas", "axe: regras violadas"),
    ("axe: ocorrências", "axe: ocorrências"),
    ("WAVE: Errors", "WAVE: Errors"),
    ("WAVE: Contrast Errors", "WAVE: Contrast Errors"),
    ("WAVE: Alerts", "WAVE: Alerts"),
    ("WAVE: AIM Score", "WAVE: AIM Score"),
    ("Lighthouse: pontuação", "Lighthouse: pontuação"),
    ("ASES: percentual", "ASES: percentual"),
    ("ASES: erros", "ASES: erros"),
    ("ASES: avisos", "ASES: avisos"),
    ("Teclado: itens atendidos", "Teclado: itens atendidos"),
]


def ler(arquivo):
    planilha = load_workbook(arquivo, data_only=True).active
    linhas = list(planilha.iter_rows(values_only=True))
    cabecalho = list(linhas[0])
    dados = {}
    for linha in linhas[1:]:
        if linha[0]:
            dados[linha[0]] = dict(zip(cabecalho, linha))
    return dados


def gravar_tabela(antes, depois):
    DESTINO.mkdir(exist_ok=True)
    cabecalho = ["Página", "Nome"]
    for _, rotulo in METRICAS:
        cabecalho += [f"{rotulo} (antes)", f"{rotulo} (depois)", f"{rotulo} (variação)"]
    with open(DESTINO / "comparativo.csv", "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(cabecalho)
        for pagina in antes:
            linha = [pagina, antes[pagina]["Nome"]]
            for coluna, _ in METRICAS:
                a = antes[pagina][coluna]
                d = depois[pagina][coluna]
                variacao = round(d - a, 2) if a is not None and d is not None else ""
                linha += [a, d, variacao]
            escritor.writerow(linha)


def total(dados, coluna):
    return sum(d[coluna] or 0 for d in dados.values())


def media(dados, coluna):
    valores = [d[coluna] for d in dados.values() if d[coluna] is not None]
    return round(sum(valores) / len(valores), 2)


def gravar_resumo(antes, depois):
    linhas = [
        ("axe: regras violadas (soma)", total(antes, "axe: regras violadas"), total(depois, "axe: regras violadas")),
        ("axe: ocorrências (soma)", total(antes, "axe: ocorrências"), total(depois, "axe: ocorrências")),
        ("WAVE: Errors (soma)", total(antes, "WAVE: Errors"), total(depois, "WAVE: Errors")),
        ("WAVE: Contrast Errors (soma)", total(antes, "WAVE: Contrast Errors"), total(depois, "WAVE: Contrast Errors")),
        ("WAVE: AIM Score (média)", media(antes, "WAVE: AIM Score"), media(depois, "WAVE: AIM Score")),
        ("Lighthouse: pontuação (média)", media(antes, "Lighthouse: pontuação"), media(depois, "Lighthouse: pontuação")),
        ("ASES: percentual (média)", media(antes, "ASES: percentual"), media(depois, "ASES: percentual")),
        ("ASES: erros (soma)", total(antes, "ASES: erros"), total(depois, "ASES: erros")),
        ("Teclado: itens atendidos (média)", media(antes, "Teclado: itens atendidos"), media(depois, "Teclado: itens atendidos")),
    ]
    with open(DESTINO / "resumo.csv", "w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(["Indicador", "Antes", "Depois"])
        escritor.writerows(linhas)


def painel(eixo, antes, depois, coluna, titulo, limite=None, rotulo_y=""):
    paginas = list(antes)
    posicoes = list(range(len(paginas)))
    largura = 0.36
    valores_a = [antes[p][coluna] or 0 for p in paginas]
    valores_d = [depois[p][coluna] or 0 for p in paginas]
    eixo.bar([x - largura / 2 - 0.02 for x in posicoes], valores_a, largura, color=COR_ANTES, label="Antes", zorder=3)
    eixo.bar([x + largura / 2 + 0.02 for x in posicoes], valores_d, largura, color=COR_DEPOIS, label="Depois", zorder=3)
    eixo.set_xticks(posicoes)
    eixo.set_xticklabels(paginas, fontsize=8, color=TEXTO_SECUNDARIO)
    eixo.set_title(titulo, fontsize=11, color=TEXTO, loc="left", fontweight="bold")
    eixo.set_ylabel(rotulo_y, fontsize=8, color=TEXTO_SECUNDARIO)
    if limite:
        eixo.set_ylim(*limite)
    eixo.grid(axis="y", color=GRADE, linewidth=0.8, zorder=0)
    eixo.tick_params(axis="y", labelsize=8, colors=TEXTO_SECUNDARIO, length=0)
    eixo.tick_params(axis="x", length=0)
    for lado in ("top", "right", "left"):
        eixo.spines[lado].set_visible(False)
    eixo.spines["bottom"].set_color(GRADE)
    maximo = max(valores_a + valores_d) or 1
    for x, a, d in zip(posicoes, valores_a, valores_d):
        if a == maximo:
            eixo.text(x - largura / 2 - 0.02, a, f"{a:g}", ha="center", va="bottom", fontsize=7, color=TEXTO)
        if d == maximo and d != a:
            eixo.text(x + largura / 2 + 0.02, d, f"{d:g}", ha="center", va="bottom", fontsize=7, color=TEXTO)


def gravar_graficos(antes, depois):
    figura, eixos = plt.subplots(3, 2, figsize=(13, 11))
    painel(eixos[0][0], antes, depois, "WAVE: Errors", "WAVE: Errors por página", rotulo_y="erros")
    painel(eixos[0][1], antes, depois, "WAVE: Contrast Errors", "WAVE: Contrast Errors por página", rotulo_y="erros de contraste")
    painel(eixos[1][0], antes, depois, "Lighthouse: pontuação", "Lighthouse: pontuação de acessibilidade", (0, 105), "pontos")
    painel(eixos[1][1], antes, depois, "ASES: percentual", "ASES: percentual de conformidade", (0, 105), "%")
    painel(eixos[2][0], antes, depois, "axe: ocorrências", "axe: ocorrências por página", rotulo_y="ocorrências")
    painel(eixos[2][1], antes, depois, "Teclado: itens atendidos", "Inspeção por teclado: itens atendidos de 11", (0, 12), "itens")
    manipuladores, rotulos = eixos[0][0].get_legend_handles_labels()
    figura.legend(manipuladores, rotulos, loc="upper right", ncol=2, frameon=False, fontsize=10)
    figura.tight_layout(rect=(0, 0, 1, 0.97))
    figura.savefig(DESTINO / "comparativo.png", dpi=160)
    plt.close(figura)


def ler_resumo(rodada):
    return pd.read_csv(RESULTADOS / rodada / "resumo.csv", dtype={"criterios": str})


def explodir_criterios(dados):
    linhas = dados.assign(criterio=dados["criterios"].fillna("").str.split(r"[;,\s]+")).explode("criterio")
    linhas["criterio"] = linhas["criterio"].str.strip()
    return linhas[linhas["criterio"] != ""]


def juntar(antes, depois, chave, medida="ocorrencias"):
    a = antes.groupby(chave)[medida].sum().rename("ocorrencias_antes")
    d = depois.groupby(chave)[medida].sum().rename("ocorrencias_depois")
    return pd.concat([a, d], axis=1).fillna(0).astype(int)


def gravar_axe(antes, depois):
    por_pagina = pd.concat(
        [
            antes.groupby("pagina").agg(regras_antes=("regra", "count"), ocorrencias_antes=("ocorrencias", "sum")),
            depois.groupby("pagina").agg(regras_depois=("regra", "count"), ocorrencias_depois=("ocorrencias", "sum")),
        ],
        axis=1,
    ).reindex([f"P{i:02d}" for i in range(1, 13)]).fillna(0).astype(int)
    por_pagina.to_csv(RESULTADOS / "comparacao_por_pagina.csv", encoding="utf-8-sig")
    por_criterio = juntar(explodir_criterios(antes), explodir_criterios(depois), "criterio")
    por_criterio.to_csv(RESULTADOS / "comparacao_por_criterio.csv", encoding="utf-8-sig")
    por_impacto = juntar(antes, depois, "impacto")
    por_impacto.to_csv(RESULTADOS / "comparacao_por_impacto.csv", encoding="utf-8-sig")
    return por_pagina, por_criterio, por_impacto


def grafico_barras(tabela, titulo, rotulo_x, arquivo, horizontal=False):
    figura, eixo = plt.subplots(figsize=(10, 5.5))
    tabela = tabela.rename(columns={"ocorrencias_antes": "Antes", "ocorrencias_depois": "Depois"})
    tabela[["Antes", "Depois"]].plot(kind="barh" if horizontal else "bar", ax=eixo, color=[COR_ANTES, COR_DEPOIS], width=0.75, zorder=3)
    eixo.set_title(titulo, fontsize=12, color=TEXTO, loc="left", fontweight="bold")
    (eixo.set_ylabel if horizontal else eixo.set_xlabel)(rotulo_x, fontsize=9, color=TEXTO_SECUNDARIO)
    (eixo.set_xlabel if horizontal else eixo.set_ylabel)("Ocorrências de violação (axe-core)", fontsize=9, color=TEXTO_SECUNDARIO)
    eixo.grid(axis="x" if horizontal else "y", color=GRADE, linewidth=0.8, zorder=0)
    eixo.tick_params(length=0, labelsize=8, colors=TEXTO_SECUNDARIO)
    if not horizontal:
        plt.setp(eixo.get_xticklabels(), rotation=0)
    for lado in ("top", "right", "left" if not horizontal else "bottom"):
        eixo.spines[lado].set_visible(False)
    eixo.legend(frameon=False, fontsize=9)
    figura.tight_layout()
    figura.savefig(RESULTADOS / arquivo, dpi=200)
    plt.close(figura)


def main():
    antes = ler(RESULTADOS / "antes" / "indicadores.xlsx")
    depois = ler(RESULTADOS / "depois" / "indicadores.xlsx")
    DESTINO.mkdir(exist_ok=True)
    gravar_tabela(antes, depois)
    gravar_resumo(antes, depois)
    gravar_graficos(antes, depois)
    axe_antes = ler_resumo("antes")
    axe_depois = ler_resumo("depois")
    por_pagina, por_criterio, por_impacto = gravar_axe(axe_antes, axe_depois)
    print(por_pagina)
    grafico_barras(por_pagina[["ocorrencias_antes", "ocorrencias_depois"]], "Ocorrências de violação por página (axe-core)", "Página", "grafico_ocorrencias_por_pagina.png")
    grafico_barras(por_criterio, "Ocorrências de violação por critério da WCAG (axe-core)", "Critério da WCAG", "grafico_ocorrencias_por_criterio.png")
    grafico_barras(por_impacto, "Ocorrências de violação por impacto (axe-core)", "Impacto", "grafico_ocorrencias_por_impacto.png")
    print(f"Arquivos gravados em {DESTINO}")


if __name__ == "__main__":
    main()
