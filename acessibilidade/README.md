# Avaliação de acessibilidade do FIND

Esta pasta guarda tudo o que foi usado para avaliar a acessibilidade da plataforma FIND antes e depois das correções, com a WCAG 2.2 (níveis A e AA) e o eMAG 3.1, seguindo o WCAG-EM. As duas rodadas usam as mesmas 12 páginas, as mesmas ferramentas e o mesmo protocolo.

## O que há na pasta

| Arquivo ou pasta | Conteúdo |
|---|---|
| `PROTOCOLO.md` | Protocolo da avaliação: ferramentas e versões, ordem de execução, inspeção por teclado (K1 a K11), definição de barreira e prioridades |
| `paginas.csv` | As 12 páginas da amostra (P01 a P12), com a URL e se exigem login |
| `criterios_wcag_emag.csv` | Critérios da WCAG e recomendações do eMAG usados na planilha de barreiras |
| `barreiras.csv` | Planilha de barreiras (B01 a B45), com critério, páginas, escopo, evidência, situação, correção e commit |
| `avaliar_axe.py` | Script que roda o axe-core em todas as páginas e grava os resultados |
| `comparar.py` | Script que compara as duas rodadas e gera as tabelas e os gráficos |
| `requirements-avaliacao.txt` | Bibliotecas Python da avaliação, com as versões fixadas |
| `resultados/antes/` | Rodada "antes" (versão da tag `a11y-antes`) |
| `resultados/depois/` | Rodada "depois" (versão da tag `a11y-depois`) |
| `resultados/comparativo/` e `resultados/comparacao_*` | Tabelas e gráficos da comparação |

Cada rodada, em `resultados/antes/` e em `resultados/depois/`, tem:

- `P01.json` a `P12.json`, `resumo.csv` e `execucao.txt`: saída do axe (violações, regras e ambiente de execução);
- `indicadores.xlsx`: uma linha por página, com axe, WAVE, Lighthouse, ASES e inspeção por teclado;
- `lighthouse/`: os 12 relatórios do Lighthouse em HTML;
- `prints/`: evidências, com o código da barreira no nome (`B02_antes.png`, `B02_depois.png`) e os prints do WAVE (`WAVE_P01.png` a `WAVE_P12.png`);
- `notas.md`: decisões e observações da rodada, para consulta na escrita dos Resultados.

## Como instalar

Requer Python 3.13 e o Edge instalado. No ambiente virtual do projeto:

```
pip install -r requirements.txt
pip install -r acessibilidade/requirements-avaliacao.txt
python -m playwright install chromium
```

O script do axe usa o canal `msedge` do Playwright. Se o Edge não abrir, troque para `chromium` na constante `CANAL` de `avaliar_axe.py`.

## Como gerar os dados fictícios

As duas rodadas usam os mesmos dados fictícios. Com o banco local migrado:

```
python manage.py popular_dados_avaliacao
```

O comando cria os usuários `avaliadora@example.com` e `visitante@example.com` (senha `Avaliacao@2026`), os itens `avaliacao-01` a `avaliacao-12` e uma conversa entre eles. A página inicial mostra o número de membros, que depende dos usuários do banco (5 nas duas rodadas, com um administrador).

## Como rodar o axe

Com o servidor local no ar (`python manage.py runserver 8000`):

```
python acessibilidade/avaliar_axe.py --rotulo antes
python acessibilidade/avaliar_axe.py --rotulo depois
```

O script entra na conta `avaliadora`, abre as 12 páginas, aplica o axe-core com as tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` e `wcag22aa`, e grava os resultados em `resultados/<rotulo>/`. Uma página que não aparece no `resumo.csv` não teve violações.

## Como refazer a rodada "antes"

A versão avaliada no "antes" está na tag `a11y-antes`:

```
git worktree add ../projeto-find-antes a11y-antes
cd ../projeto-find-antes
python manage.py runserver 8001
```

As demais ferramentas (WAVE, Lighthouse, ASES Web e a inspeção por teclado) são aplicadas página a página, como descrito em `PROTOCOLO.md`, e os números vão para `indicadores.xlsx`.

## Como gerar as tabelas e os gráficos

```
python acessibilidade/comparar.py
```

O script lê os `resumo.csv` e os `indicadores.xlsx` das duas rodadas e grava:

| Arquivo | O que mostra |
|---|---|
| `resultados/comparacao_por_pagina.csv` | Regras violadas e ocorrências do axe, por página, antes e depois |
| `resultados/comparacao_por_criterio.csv` | Ocorrências do axe por critério da WCAG, antes e depois |
| `resultados/comparacao_por_impacto.csv` | Ocorrências do axe por impacto, antes e depois |
| `resultados/grafico_ocorrencias_por_pagina.png`, `..._por_criterio.png`, `..._por_impacto.png` | Gráficos das três tabelas acima |
| `resultados/comparativo/comparativo.csv` | Todos os indicadores por página (axe, WAVE, Lighthouse, ASES e teclado), com antes, depois e variação |
| `resultados/comparativo/resumo.csv` | Somas e médias de cada indicador |
| `resultados/comparativo/comparativo.png` | Gráficos por página do WAVE, Lighthouse, ASES, axe e teclado |

Uma página sem violações no "depois" aparece com zero, e não como página ausente.

## Unidades de medida

Cada ferramenta mede de um jeito, e os números só se comparam dentro da mesma ferramenta, entre o antes e o depois: o axe conta regras violadas e ocorrências, o WAVE conta Errors e Contrast Errors, o Lighthouse dá uma pontuação de 0 a 100, o ASES dá um percentual de conformidade e a inspeção por teclado conta itens atendidos de 11.

## Observações

- A P08 (cadastro de item) é um modal. O WAVE e a inspeção por teclado foram feitos com o modal aberto sobre `/menu/`, e o axe, o Lighthouse e o ASES usaram a URL do fragmento (`/perfil/item/novo/`). A nota do Lighthouse da P08 não é comparável com a das outras páginas.
- A planilha `barreiras.csv` tem 45 barreiras, todas "Corrigida". A avaliação inicial tem 36 delas, e as outras 9 foram encontradas durante as correções e a rodada "depois" (veja `resultados/antes/notas.md` e `resultados/depois/notas.md`).
- Os 3 testes automatizados de autenticação que já falhavam antes (`pytest`) não fazem parte desta avaliação e não foram alterados.
