# Protocolo de avaliação de acessibilidade do FIND

Este documento descreve como será feita a avaliação de acessibilidade da plataforma web do FIND. Ele foi escrito antes da primeira avaliação e deve ser seguido do mesmo jeito na rodada feita depois das correções, para que a comparação entre as duas seja justa.

A avaliação toma como referência a WCAG 2.2 (níveis A e AA) e o eMAG 3.1, e segue a metodologia WCAG-EM 2.0, da W3C. O escopo são as páginas públicas e as páginas do usuário comum. O aplicativo móvel, os painéis de bolsista, administrador e IoT e os testes com leitor de tela ficam fora desta rodada.

## 1. Amostra e dados

A amostra é formada pelas páginas listadas em `paginas.csv`, escolhidas para cobrir os principais fluxos do usuário comum e os tipos de componente do sistema (formulário, lista, detalhe, chat e upload).

| ID | Página | URL | Perfil |
|---|---|---|---|
| P01 | Página inicial | `/` | sem login |
| P02 | Entrar | `/login/` | sem login |
| P03 | Cadastro de usuário | `/register/` | sem login |
| P04 | Redefinir senha | `/redefinir-senha/` | sem login |
| P05 | Início (menu) | `/menu/` | avaliadora |
| P06 | Itens perdidos | `/itens/perdidos/` | avaliadora |
| P07 | Detalhe do item | `/item/avaliacao-01/` | avaliadora (dona do item) |
| P08 | Cadastrar item | `/perfil/item/novo/` | avaliadora |
| P09 | Meus chats | `/chats/` | avaliadora |
| P10 | Conversa | `/chats/1/` | avaliadora |
| P11 | Perfil do usuário | `/tela/` | avaliadora |
| P12 | Busca visual | `/itens/busca-visual/` | avaliadora |
| P13 | Detalhe do item (visitante) | `/item/avaliacao-01/` | visitante |

A P13 foi incluída por decisão do autor, porque a página de detalhe muda conforme quem a acessa: a dona do item vê os dados de contato e os controles de status, enquanto o visitante vê o botão para iniciar a conversa. A decisão será informada ao orientador na entrega da sprint e, se ele preferir, a P13 sai da análise sem afetar as outras doze páginas. A visão da página de detalhe sem login não será avaliada e entra como limitação do trabalho.

A WCAG-EM 2.0 também sugere uma amostra aleatória, de cerca de 10% do tamanho da amostra estruturada, o que daria uma ou duas páginas a mais. A inclusão dela está pendente de decisão do orientador.

Os dados usados na avaliação são fictícios e criados pelo comando `popular_dados_avaliacao`, depois de `criar_categorias`. Ele cria dois usuários (`avaliadora` e `visitante`), doze itens e uma conversa, sempre com o mesmo conteúdo, e o banco não é alterado durante a rodada. A versão avaliada fica registrada na tag `a11y-antes` (e `a11y-depois` na segunda rodada).

## 2. Ferramentas e versões

A avaliação automática usa quatro ferramentas, com as versões e configurações abaixo.

| Ferramenta | Versão | Configuração |
|---|---|---|
| axe-core, pelo script `avaliar_axe.py` | 4.12.1 (axe-playwright-python 0.1.8, Playwright 1.63.0) | tags wcag2a, wcag2aa, wcag21a, wcag21aa e wcag22aa |
| axe DevTools | 4.138.0 (axe-core 4.13.0) | usado só para localizar o elemento no template |
| WAVE | 3.3.1.0 | registro de Errors, Contrast Errors, Alerts e AIM Score |
| Lighthouse | 13.4.1 | janela anônima sem extensões, modo Navegação, Desktop e só a categoria Acessibilidade |
| ASES Web | sem versão numerada, com a data de acesso anotada | páginas com login avaliadas pelo código-fonte |

Para o axe, a contagem oficial do trabalho é a do script. A extensão axe DevTools serve apenas para encontrar onde, no template, está o problema apontado. O ambiente usa Python 3.13.15 e Django 6.0.3, e as bibliotecas da avaliação estão fixadas em `requirements-avaliacao.txt`.

## 3. Ordem de execução, navegador e resolução

Antes de começar, os dados são recriados e o servidor local é iniciado. Primeiro roda-se o script do axe em todas as páginas de uma vez (`python acessibilidade/avaliar_axe.py --rotulo antes`). Depois, em cada página, usa-se o WAVE, o Lighthouse, o ASES Web e, por último, o checklist de teclado.

Tudo é feito no Edge, com resolução de 1366 x 768. O script usa o canal `msedge` do Playwright.

## 4. Inspeção por teclado

A parte manual da avaliação é feita só com o teclado, sem leitor de tela. Em cada página, cada item abaixo é marcado como Atende, Não atende ou Não se aplica.

| # | Verificação | Critério WCAG |
|---|---|---|
| K1 | Tudo o que é clicável recebe foco com Tab | 2.1.1 |
| K2 | Nenhum componente prende o foco | 2.1.2 |
| K3 | A ordem do foco segue a ordem visual | 2.4.3 |
| K4 | O foco é visível | 2.4.7 |
| K5 | O foco não fica escondido atrás da barra fixa ou do banner | 2.4.11 |
| K6 | Existe link para pular ao conteúdo | 2.4.1 |
| K7 | Menus e modais abrem com Enter ou Espaço e fecham com Esc | 2.1.1 |
| K8 | Mostrar senha, abas, upload e filtros funcionam pelo teclado | 2.1.1 e 2.5.7 |
| K9 | Com zoom de 200% nada fica cortado | 1.4.4 |
| K10 | Com 320 px de largura não há rolagem horizontal | 1.4.10 |
| K11 | O título da aba identifica a página | 2.4.2 |

## 5. O que conta como barreira

Considera-se uma barreira um problema de um mesmo componente em um mesmo critério da WCAG. Quando o problema vem do `base.html` e aparece em várias páginas, ele conta como uma única barreira, que afeta todas elas. O mesmo vale quando mais de uma ferramenta aponta o mesmo problema: ele é registrado uma vez, com todas as ferramentas que o detectaram.
