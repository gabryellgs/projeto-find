import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # gera os gráficos sem abrir janela
import matplotlib.pyplot as plt
import pandas as pd
from django.core.management.base import BaseCommand

from correspondencia.estrategias import B0, F, STATUS_CANDIDATOS, T1, V, histograma
from correspondencia.metricas import mrr, posicao_do_correto, recall_em_k
from correspondencia.models import ParGabarito
from items.models import Item

RESULTADOS = Path(__file__).resolve().parents[2] / "resultados"


def resumir(posicoes, colunas):
    """Calcula as métricas agrupando as posições pelas colunas indicadas."""
    return (
        posicoes.groupby(colunas, sort=False)["posicao"]
        .agg(
            consultas="count",
            recall_1=lambda p: recall_em_k(list(p), 1),
            recall_6=lambda p: recall_em_k(list(p), 6),
            mrr=lambda p: mrr(list(p)),
        )
        .round(3)
        .reset_index()
    )


class Command(BaseCommand):
    help = "Roda as estratégias e gera as tabelas e os gráficos em resultados/."

    def add_arguments(self, parser):
        parser.add_argument("--tempo", action="store_true", help="Mede o tempo de resposta.")

    def handle(self, *args, **opcoes):
        RESULTADOS.mkdir(exist_ok=True)
        candidatos = list(Item.objects.filter(status__in=STATUS_CANDIDATOS))
        pares = list(ParGabarito.objects.select_related("perdido", "achado"))

        if opcoes["tempo"]:
            self.medir_tempo(candidatos, pares)
            return

        estrategias = [B0(), T1(), V(), F(usar_foto=True), F(usar_foto=False)]

        # 1. Posição do achado correto para cada perdido e cada estratégia.
        linhas = []
        for estrategia in estrategias:
            self.stdout.write(f"Rodando {estrategia.nome}...")
            estrategia.preparar(candidatos)
            for par in pares:
                pontuacoes = estrategia.pontuar(par.perdido)
                linhas.append({
                    "estrategia": estrategia.nome,
                    "perdido_id": par.perdido_id,
                    "posicao": posicao_do_correto(pontuacoes, par.achado_id),
                    "pontuacao_correto": round(pontuacoes[par.achado_id], 3),
                    "variacao": par.variacao,
                    "objeto_parecido": par.objeto_parecido,
                })
        posicoes = pd.DataFrame(linhas)
        posicoes.to_csv(RESULTADOS / "posicoes.csv", index=False)

        # 2. Tabela principal.
        metricas = resumir(posicoes, ["estrategia"])
        metricas.to_csv(RESULTADOS / "metricas.csv", index=False)
        self.stdout.write(metricas.to_string(index=False))

        # 3. Quantas vezes o FIND de hoje nem mostraria o correto (pontuação abaixo de 30).
        b0 = posicoes[posicoes["estrategia"] == "B0"]
        abaixo = int((b0["pontuacao_correto"] < 0.30).sum())
        self.stdout.write(f"\nB0: correto abaixo de 0,30 em {abaixo} de {len(b0)} perdidos")

        # 4. Robustez: métricas por grupo de variação e por objeto parecido.
        resumir(posicoes, ["estrategia", "variacao"]).to_csv(RESULTADOS / "robustez_variacao.csv", index=False)
        resumir(posicoes, ["estrategia", "objeto_parecido"]).to_csv(RESULTADOS / "robustez_parecido.csv", index=False)

        # 5. Gráficos (PNG, 300 dpi).
        graficos = RESULTADOS / "graficos"
        graficos.mkdir(exist_ok=True)

        eixo = metricas.set_index("estrategia")[["recall_1", "recall_6", "mrr"]].plot.bar(rot=0)
        eixo.set_xlabel("Estratégia")
        eixo.set_ylabel("Valor da métrica")
        eixo.set_ylim(0, 1)
        plt.tight_layout()
        plt.savefig(graficos / "metricas.png", dpi=300)
        plt.close()

        robustez = resumir(posicoes, ["estrategia", "variacao"])
        # Filtra só as estratégias relevantes para o gráfico de robustez.
        colunas_grafico = [c for c in ["B0", "T1", "F", "F (sem foto)"] if c in robustez["estrategia"].values]
        tabela = robustez.pivot(index="variacao", columns="estrategia", values="recall_6")
        if colunas_grafico:
            eixo = tabela[colunas_grafico].plot.bar(rot=0)
            eixo.set_xlabel("Variação no texto do perdido")
            eixo.set_ylabel("Recall@6")
            eixo.set_ylim(0, 1)
            plt.tight_layout()
            plt.savefig(graficos / "robustez.png", dpi=300)
            plt.close()

        self.stdout.write(self.style.SUCCESS("\nResultados salvos em correspondencia/resultados/"))

    def medir_tempo(self, candidatos, pares):
        # 1.000 achados extras só de texto: os distratores (sem foto) repetidos.
        distratores = [c for c in candidatos if not c.imagem]
        if not distratores:
            self.stdout.write(self.style.WARNING("Nenhum distrator sem foto encontrado para gerar extras."))
            distratores = candidatos[:10]  # fallback
        repeticoes = max(1, 1000 // len(distratores))
        extras = [
            Item(id=1_000_000 + i, titulo=d.titulo, descricao=d.descricao,
                 categoria=d.categoria, status="achado")
            for i, d in enumerate(distratores * repeticoes)
        ]
        todos = candidatos + extras

        linhas = []
        for estrategia in [B0(), T1(), F(usar_foto=False)]:
            inicio = time.perf_counter()
            estrategia.preparar(todos)
            preparar_ms = (time.perf_counter() - inicio) * 1000

            tempos = []
            for par in pares[:31]:
                inicio = time.perf_counter()
                estrategia.pontuar(par.perdido)
                tempos.append((time.perf_counter() - inicio) * 1000)
            tempos = tempos[1:]  # descarta a primeira consulta (aquecimento)

            linhas.append({
                "estrategia": estrategia.nome,
                "candidatos": len(todos),
                "preparar_ms": round(preparar_ms, 1),
                "consulta_ms": round(sum(tempos) / len(tempos), 1),
            })

        # Parte da imagem: tempo de calcular o histograma de uma foto (média de até 10 fotos).
        pares_com_foto = [p for p in pares if p.perdido.imagem and p.perdido.image_hash]
        if pares_com_foto:
            tempos = []
            for par in pares_com_foto[:10]:
                inicio = time.perf_counter()
                histograma(par.perdido)
                tempos.append((time.perf_counter() - inicio) * 1000)
            linhas.append({"estrategia": "V (histograma de 1 foto)", "candidatos": 1,
                           "preparar_ms": None, "consulta_ms": round(sum(tempos) / len(tempos), 1)})

        RESULTADOS.mkdir(exist_ok=True)
        tabela = pd.DataFrame(linhas)
        tabela.to_csv(RESULTADOS / "tempos.csv", index=False)
        self.stdout.write(tabela.to_string(index=False))

