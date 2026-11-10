# Notas da rodada "antes"

Registro de decisões tomadas durante a avaliação, para consulta na escrita dos Resultados.

## Dados e ambiente

- Os dados fictícios foram criados com `popular_dados_avaliacao` antes da rodada. O comando foi executado de novo em 10/11/2026, ao subir o servidor para as inspeções manuais, e um usuário administrador foi criado no banco local. O conteúdo das páginas não mudou. Mudaram apenas o contador de membros da página inicial (de 4 para 5) e o horário das mensagens da conversa.
- O arquivo `execucao.txt` foi recriado em 10/11/2026 a partir da saída do terminal da rodada de 09/11/2026.

## P08, cadastro de item

- Na interface, o cadastro de item existe como um modal aberto por cima de outra página. A URL `/perfil/item/novo/` devolve só o código do modal, sem `<title>`, sem `lang` e sem as folhas de estilo da página.
- O WAVE e o teclado foram feitos com o modal aberto sobre `/menu/`. O axe, o Lighthouse e o ASES usaram a URL da amostra, que devolve o fragmento. Para o ASES, o fragmento foi envolvido em uma estrutura mínima de documento HTML, porque o avaliador recusa código sem `<html>`.
- A nota 41 do Lighthouse da P08 não é comparável com a das outras páginas, pelo mesmo motivo.

## Achados descartados

| Achado | Ferramenta | Páginas | Motivo |
|---|---|---|---|
| document-title | axe, Lighthouse | P08 | Efeito do fragmento: a página real tem título. |
| html-has-lang | axe, Lighthouse | P08 | Efeito do fragmento: a página real tem idioma. |
| aria-hidden-focus | axe, Lighthouse | P08 | Efeito do fragmento. O modal tem `aria-hidden="true"` e, sem o CSS do Bootstrap, fica visível e focável. Na página real, onde o modal está embutido (P05 a P12), ele fica com `display: none` até ser aberto, e o axe não acusa o problema. |
| landmark-one-main | Lighthouse | P08 | Efeito do fragmento, que não tem `<main>`. Nas outras páginas, o `<main>` vem do `base.html`. |

## Regras de boas práticas do axe que entraram como barreira

Algumas regras são classificadas como boas práticas pelo axe, e não como critérios da WCAG. Entraram na planilha quando tinham critério da WCAG e recomendação do eMAG correspondentes:

- B23, títulos pulados (`heading-order`): critério 1.3.1, eMAG 1.3, também apontado pelo WAVE e pelo ASES.
- B25, página inicial sem região principal (`landmark-one-main`): critério 1.3.1, eMAG 1.8, também apontado pelo ASES.
- B31, diálogo sem nome (`aria-dialog-name`, P09): critério 4.1.2, apontado só pelo Lighthouse. O script do axe não o lista porque a regra, nessa versão, é de boas práticas. O elemento é o `div#chatModalBackdrop` (`role="dialog"`), que fica sempre no DOM, com `opacity: 0` e sem `display: none` quando está fechado.

## Alertas do WAVE que não viraram barreira

Os alertas de texto muito pequeno, link redundante e alternativa redundante são avisos, e não violações de critério, e por isso ficaram fora da planilha.

## Critério 2.4.11

No FIND, o elemento que cobre o foco do teclado é o banner de cookies, fixo na parte de baixo da tela. A barra de navegação não cobre o foco.

## Critério 2.5.8

O axe DevTools da extensão avalia a WCAG 2.1 AA e não detecta o tamanho do alvo, que é da 2.2. O B24 foi detectado pelo axe com as tags da 2.2 e pelo Lighthouse.

## Título vazio na P11 (B22)

O título vazio aparece porque o usuário `avaliadora` foi criado sem nome. Uma conta real também pode ficar sem nome: o servidor não valida o nome no cadastro nem na edição de perfil (a obrigatoriedade existe só no HTML, e o formulário de cadastro tem `novalidate`), e o login social depende do nome devolvido pelo provedor.
