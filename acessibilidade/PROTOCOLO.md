# Protocolo de avaliação de acessibilidade do FIND

Este documento descreve como será feita a avaliação de acessibilidade da plataforma web do FIND. Ele foi escrito antes da primeira avaliação e deve ser seguido do mesmo jeito na rodada feita depois das correções, para que a comparação entre as duas seja justa.

A avaliação toma como referência a WCAG 2.2 (níveis A e AA) e o eMAG 3.1, e segue a metodologia WCAG-EM 2.0, da W3C. O escopo são as páginas públicas e as páginas do usuário comum. O aplicativo móvel, os painéis de bolsista, administrador e IoT e os testes com usuários ficam fora desta rodada. A inspeção manual é feita pelo autor, com teclado e com leitor de tela (NVDA, no Edge), e não deve ser confundida com um teste com usuários.

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
| P07 | Detalhe do item | `/item/avaliacao-01/` | avaliadora (dono do item) |
| P08 | Cadastrar item | `/perfil/item/novo/` | avaliadora |
| P09 | Meus chats | `/chats/` | avaliadora |
| P10 | Conversa | `/chats/1/` | avaliadora |
| P11 | Perfil do usuário | `/tela/` | avaliadora |
| P12 | Busca visual | `/itens/busca-visual/` | avaliadora |

A página de detalhe muda conforme quem a acessa: o dono do item vê os dados de contato e os controles de status, o visitante logado vê o botão para iniciar a conversa e quem não tem login vê o link para entrar. A P07 é avaliada só na visão do dono do item. As visões do visitante e de quem não tem login ficam de fora e entram como limitação do trabalho.

A WCAG-EM 2.0 também sugere uma amostra aleatória, de cerca de 10% do tamanho da amostra estruturada, o que daria uma ou duas páginas a mais. A inclusão dela está pendente de decisão do orientador.

Os dados usados na avaliação são fictícios e criados pelo comando `popular_dados_avaliacao`, depois de `criar_categorias`. Ele cria dois usuários (`avaliadora` e `visitante`), doze itens e uma conversa, sempre com o mesmo conteúdo, e o banco não é alterado durante a rodada. A versão avaliada fica registrada na tag `a11y-antes` (e `a11y-depois` na segunda rodada).

## 2. Ferramentas e versões

A avaliação usa as ferramentas abaixo, com as versões e configurações indicadas.

| Ferramenta | Versão | Configuração |
|---|---|---|
| axe-core, pelo script `avaliar_axe.py` | 4.12.1 (axe-playwright-python 0.1.8, Playwright 1.63.0) | tags wcag2a, wcag2aa, wcag21a, wcag21aa e wcag22aa |
| axe DevTools | 4.138.0 (axe-core 4.13.0) | usado só para localizar o elemento no template |
| WAVE | 3.3.1.0 | registro de Errors, Contrast Errors, Alerts e AIM Score |
| Lighthouse | 13.4.1 | rodado pelo script `avaliar_lighthouse.py`, com Edge de perfil novo e sem extensões, modo Navegação, preset Desktop e só a categoria Acessibilidade; nas páginas com login o script envia o cookie de sessão |
| ASES Web | sem versão numerada, com a data de acesso anotada | páginas com login avaliadas pelo código-fonte, salvo pelo script `salvar_html_ases.py` |
| NVDA | anotada no início de cada rodada | no Edge; sintetizador e voz também anotados no início da rodada; modo de navegação para ler a página e modo de foco nos campos de formulário |
| Edge | 157.0.4341.42 | navegador de todas as ferramentas; a versão é anotada no início de cada rodada |

Para o axe, a contagem oficial do trabalho é a do script. A extensão axe DevTools serve apenas para encontrar onde, no template, está o problema apontado. O ambiente usa Python 3.13.15 e Django 6.0.3, e as bibliotecas da avaliação estão fixadas em `requirements-avaliacao.txt`.

## 3. Ordem de execução, navegador e resolução

Antes de começar, os dados são recriados e o servidor local é iniciado. Primeiro roda-se o script do axe em todas as páginas de uma vez (`python acessibilidade/avaliar_axe.py --rotulo antes`). O Lighthouse também roda por script (`python acessibilidade/avaliar_lighthouse.py --rotulo antes`), e o código-fonte das páginas com login, para o ASES Web, é salvo por outro (`python acessibilidade/salvar_html_ases.py --rotulo antes`). Depois, em cada página, usa-se o WAVE, o ASES Web, o checklist de teclado e, por último, o checklist do NVDA.

Tudo é feito no Edge, com resolução de 1366 x 768. O script usa o canal `msedge` do Playwright.

## 4. Inspeção por teclado

A inspeção manual começa pelo teclado, sem o mouse. Em cada página, cada item abaixo é marcado como Atende, Não atende ou Não se aplica.

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

## 5. Inspeção com leitor de tela

Depois do checklist de teclado, cada página é inspecionada com o leitor de tela NVDA, no Edge. A versão, o sintetizador e a voz, e os modos usados estão na seção 2. A inspeção é feita pelo autor e não substitui um teste com usuários que usam leitor de tela: o resultado depende de quem a conduz, e isso entra nas limitações do trabalho. Cada item é marcado como Atende, Não atende ou Não se aplica. Como evidência, usa-se o Visualizador de Fala do NVDA (menu do NVDA, Ferramentas), com um print do que foi anunciado.

| # | Verificação | Critério WCAG | Como verificar |
|---|---|---|---|
| L1 | O título da página é lido ao carregar | 2.4.2 | ouvir ao carregar a página; NVDA+T repete o título |
| L2 | A página é lida com a voz em português | 3.1.1 | NVDA+seta para baixo lê a página e confere a pronúncia |
| L3 | A ordem de leitura, com a seta para baixo, segue a ordem visual | 1.3.2 | seta para baixo no modo de navegação, comparando com a tela |
| L4 | Os cabeçalhos (tecla H) refletem a estrutura da página | 1.3.1 e 2.4.6 | H e Shift+H percorrem os títulos; NVDA+F7 lista os títulos |
| L5 | Cabeçalho, navegação, conteúdo principal e rodapé aparecem como regiões (tecla D) | 1.3.1 | D e Shift+D percorrem as regiões; NVDA+F7 lista os pontos de referência |
| L6 | Imagens informativas têm texto alternativo e as decorativas são ignoradas | 1.1.1 | G e Shift+G percorrem as imagens |
| L7 | Links e botões, inclusive os só com ícone, são lidos com um nome que diz o destino ou a ação | 2.4.4 e 4.1.2 | K percorre os links e B os botões; NVDA+F7 lista os links |
| L8 | Campos de formulário anunciam o rótulo e se são obrigatórios | 1.3.1, 3.3.2 e 4.1.2 | F ou Tab percorrem os campos |
| L9 | Menus, modais, abas e o botão de mostrar senha anunciam o papel e o estado (aberto, fechado, selecionado) | 4.1.2 | acionar cada componente com Enter ou Espaço e ouvir o anúncio |
| L10 | Mensagens de erro e de sucesso, novas mensagens do chat e o resultado da busca visual são anunciados sem mover o foco | 3.3.1 e 4.1.3 | provocar cada situação com o foco parado e ouvir o anúncio |

## 6. O que conta como barreira

Considera-se uma barreira um problema de um mesmo componente em um mesmo critério da WCAG. Quando o problema vem do `base.html` e aparece em várias páginas, ele conta como uma única barreira, que afeta todas elas. O mesmo vale quando mais de uma ferramenta aponta o mesmo problema: ele é registrado uma vez, com todas as ferramentas que o detectaram.

## 7. Unidades de medida

Cada ferramenta mede de um jeito, e os números de uma não podem ser comparados com os de outra.

| Ferramenta | Unidade |
|---|---|
| axe | regras violadas e ocorrências |
| WAVE | Errors e Contrast Errors |
| Lighthouse | pontuação de 0 a 100 |
| ASES | percentual de conformidade |
| Checklists de teclado e de NVDA | itens atendidos |

As unidades só se comparam dentro da mesma ferramenta, entre o antes e o depois.

## 8. Ordem de prioridade das correções

1. Barreiras que impedem o uso.
2. Barreiras globais, que vêm do `base.html`.
3. Número de páginas afetadas.
4. Impacto.
