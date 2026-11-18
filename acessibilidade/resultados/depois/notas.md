# Notas da rodada "depois"

Registro de decisões tomadas durante a reavaliação, para consulta na escrita dos Resultados.

## Dados e ambiente

- Os dados fictícios foram recriados com `popular_dados_avaliacao` em 17/11/2026, antes da rodada. O usuário administrador já existia no banco local, e a página inicial mostra 5 membros, como no "antes". O conteúdo das páginas não mudou. Mudou apenas o horário das mensagens da conversa (17/11 14:31).
- A tag `a11y-depois` marca o commit final da rodada, que inclui as correções da B42, B44 e B45, achadas durante esta rodada.
- O Edge passou da versão 157.0.4341.42 (rodada "antes") para a 157.0.4341.60. As demais ferramentas mantiveram as versões: axe-core 4.12.1, WAVE 3.3.1.0 e Lighthouse 13.5.0. O ASES Web não tem versão numerada, e as avaliações foram feitas em 17/11/2026, entre 21:10 e 21:23.
- O axe foi executado em 17/11/2026 às 14:32 e repetido em 18/11/2026 às 12:02 na versão final, com o mesmo resultado. O WAVE, o Lighthouse e o ASES foram aplicados depois da correção da B41 (commit `ef91484`) e antes das correções da B42 a B45. Só o Lighthouse da P08 foi refeito depois da B42. A conferência dessa diferença está na seção "Versão avaliada e a tag".

## P08, cadastro de item

- Como no "antes", o WAVE e a inspeção por teclado foram feitos com o modal aberto sobre `/menu/`. O axe, o Lighthouse e o ASES usaram a URL do fragmento (`/perfil/item/novo/`), e para o ASES o fragmento foi envolvido em uma estrutura mínima de documento HTML.
- A nota 41 do Lighthouse da P08 é igual à do "antes", com os mesmos quatro itens (`aria-hidden-focus`, `document-title`, `html-has-lang` e `landmark-one-main`), que são efeito do fragmento. Ela não é comparável com a das outras páginas.
- O axe apontou, na P08, as mesmas três regras descartadas no "antes" (`aria-hidden-focus`, `document-title` e `html-has-lang`), que vêm do fragmento.

## Resultado do WAVE

As 12 páginas ficaram com 0 Errors e 0 Contrast Errors. Os alertas que sobraram são texto muito pequeno, link redundante e alternativa redundante, que não viraram barreira, como no "antes".

## Achados do ASES que não viraram barreira

O ASES continuou apontando alguns erros nas 12 páginas. Eles foram conferidos no código das páginas e vêm de limitações da ferramenta, e não de barreiras:

- Recomendação 2.1 (teclado): ocorrências em elementos `<img>` com `onerror`, que é um fallback de imagem e não um controle clicável.
- Recomendação 6.2 (etiquetas): o ASES não reconhece `aria-label` nos campos de busca nem a associação de `<label>` que envolve os rádios dos filtros.
- Recomendação 1.2 (marcação, crítico): links só com ícone, como as redes sociais do rodapé, que têm `aria-label`, ignorado pelo ASES.
- Recomendação 1.5 (âncoras): o ASES continuou apontando um erro em todas as páginas, mesmo com o link "Pular para o conteúdo" no início do `body`, que leva ao `main#conteudo-principal`. O critério que o ASES usa não ficou claro.
- Recomendação 4.4 (foco visível), só na P01: o CSS não remove o contorno do foco, e o ASES provavelmente procura uma regra `:focus` no CSS.

## Inspeção por teclado

Os itens K1 a K11 foram verificados nas 12 páginas. Na primeira passada, três pontos foram registrados como não atendidos: o K5 na P05 (botão flutuante sobre os chips, B43) e na P08 (B44) e o K4 na P12 (B45). A B44 e a B45 foram corrigidas. A B43 foi descartada, porque o K5 só reprova quando o foco fica totalmente escondido e o chip nunca ficou. O resultado final é de 11 itens atendidos em todas as páginas.

Na P05, os botões de próximo e anterior dos carrosséis aparecem como desabilitados conforme a posição do carrossel (o próximo fica desabilitado no último slide), e por isso não recebem o foco nessa posição. Isso não é barreira.

## Versão avaliada e a tag

O HTML das 12 páginas foi comparado entre o commit `ef91484`, em que o WAVE, o Lighthouse e o ASES foram aplicados, e o commit final da tag `a11y-depois`. As páginas P01 a P04 são idênticas. Nas páginas P05 a P12, as diferenças são: `aria-labelledby` e `id` do título nos modais que ficam fechados, duas regras de CSS de `scroll-padding`, uma linha de JavaScript removida do `base.html`, um contorno de foco no campo de foto da P12 e o número de versão dos arquivos CSS. Nenhuma delas muda texto, cor, imagem, campo ou botão visível. Por isso o orientador decidiu, em 18/11/2026, manter os dados dessas três ferramentas sem refazê-los, e eles valem para a versão final.

## Critério 2.5.7

Em 18/11/2026, na versão da tag `a11y-depois`, as funções que aceitam arrastar continuam funcionando com cliques simples: os botões e os pontos dos carrosséis da P05, o clique no mapa do cadastro de item (P08) e o clique na área de envio da foto da busca visual (P12). O resultado é o mesmo da versão `a11y-antes`, e o critério foi atendido nas 12 páginas.

## B42, B44 e B45

As barreiras B42 (modais sem nome acessível quando abertos), B44 (banner de cookies sobre os botões e o mapa dos modais) e B45 (campo de foto da busca visual sem indicador de foco) foram encontradas nesta rodada, fora da avaliação inicial, e não entram nos números dela. A B43 (botão flutuante Cadastrar item sobre os chips de categoria) foi registrada na rodada e descartada, como explicado em `resultados/antes/notas.md`. As evidências "antes" foram tiradas na versão da tag `a11y-antes`. Os detalhes estão em `resultados/antes/notas.md`.

## Totais de barreiras

São 44 barreiras no total, todas com situação "Corrigida" e com o hash do commit, mais a B43, com situação "Descartada". A avaliação inicial tem 36 barreiras (B01 a B32, B36, B39, B40 e B41). As outras 8 (B33, B34, B35, B37, B38, B42, B44 e B45) foram encontradas durante as correções e a rodada "depois".
