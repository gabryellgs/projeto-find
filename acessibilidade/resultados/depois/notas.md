# Notas da rodada "depois"

Registro de decisões tomadas durante a reavaliação, para consulta na escrita dos Resultados.

## Dados e ambiente

- Os dados fictícios foram recriados com `popular_dados_avaliacao` em 17/11/2026, antes da rodada. O usuário administrador já existia no banco local, e a página inicial mostra 5 membros, como no "antes". O conteúdo das páginas não mudou. Mudou apenas o horário das mensagens da conversa (17/11 14:31).
- A tag `a11y-depois` marca o commit final da rodada, que inclui as correções da B42 a B45, achadas durante esta rodada.
- O Edge passou da versão 157.0.4341.42 (rodada "antes") para a 157.0.4341.60. As demais ferramentas mantiveram as versões: axe-core 4.12.1, WAVE 3.3.1.0 e Lighthouse 13.5.0. O ASES Web não tem versão numerada, e as avaliações foram feitas em 17/11/2026, entre 21:10 e 21:23.
- O axe foi executado em 17/11/2026 às 14:32. O WAVE, o Lighthouse e o ASES foram feitos depois da correção da B41 e antes da B42. As correções da B42 a B45 mexem em nome de diálogo e em foco. Só o Lighthouse da P08 foi refeito depois da B42, e o WAVE, o ASES e os demais relatórios do Lighthouse não foram refeitos.

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

Os itens K1 a K11 foram verificados nas 12 páginas. Na primeira passada, três pontos não atenderam: o K5 na P05 (B43) e na P08 (B44) e o K4 na P12 (B45). As três foram corrigidas e o resultado final é de 11 itens atendidos em todas as páginas.

Na P05, os botões de próximo e anterior dos carrosséis aparecem como desabilitados conforme a posição do carrossel (o próximo fica desabilitado no último slide), e por isso não recebem o foco nessa posição. Isso não é barreira.

## B42, B43, B44 e B45

As barreiras B42 (modais sem nome acessível quando abertos), B43 (botão flutuante Cadastrar item sobre os chips de categoria), B44 (banner de cookies sobre os botões e o mapa dos modais) e B45 (campo de foto da busca visual sem indicador de foco) foram encontradas nesta rodada, fora da avaliação inicial, e não entram nos números dela. As evidências "antes" foram tiradas na versão da tag `a11y-antes`. Os detalhes estão em `resultados/antes/notas.md`.

## Totais de barreiras

São 45 barreiras no total, todas com situação "Corrigida" e com o hash do commit. A avaliação inicial tem 36 barreiras (B01 a B32, B36, B39, B40 e B41). As outras 9 (B33, B34, B35, B37, B38, B42, B43, B44 e B45) foram encontradas durante as correções e a rodada "depois".
