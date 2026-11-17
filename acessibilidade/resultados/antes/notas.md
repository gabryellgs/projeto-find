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

## B32 e o item K7 do checklist

O K7 diz que os controles abrem com Enter ou Espaço. O sino de notificações abre com Enter, por isso o K7 continua como "Atende". A B32 (o sino não abre com a tecla Espaço) apareceu em um teste complementar de teclado feito em 10/11/2026, fora do checklist: com o foco no sino, em `/menu/`, foi apertada a tecla Espaço e o painel não abriu. Esse teste não altera a marcação do K7.

## Lighthouse

Os relatórios gerados pela linha de comando em 09/11/2026 (Lighthouse 13.4.1) foram substituídos em 10/11/2026 pelos gerados no DevTools do Edge (Lighthouse 13.5.0), na versão da tag `a11y-antes` e com os mesmos dados. A pontuação e os itens reprovados das 12 páginas ficaram iguais, e por isso o `indicadores.xlsx` e o `barreiras.csv` não mudaram.

## ASES Web

O código colado no ASES Web na rodada "antes" foi a resposta do servidor a cada página, que é o mesmo conteúdo do Ctrl+U. Por isso o ASES não foi refeito.

## Título vazio na P11 (B22)

O título vazio aparece porque o usuário `avaliadora` foi criado sem nome. Uma conta real também pode ficar sem nome: o servidor não valida o nome no cadastro nem na edição de perfil (a obrigatoriedade existe só no HTML, e o formulário de cadastro tem `novalidate`), e o login social depende do nome devolvido pelo provedor.

## Omissões da consolidação (B36, B39, B40 e B41)

A B36 (foto do modal Editar perfil sem texto alternativo), a B39 (campo de busca da P09 sem rótulo), a B40 (P11 sem título de primeiro nível) e a B41 (aviso de cookies salvos, escondido com opacidade zero, contado pelo WAVE como erro de contraste) foram apontadas pelo WAVE na rodada inicial, mas ficaram fora da planilha na consolidação. As evidências são os prints da própria rodada: `WAVE_P05.png` a `WAVE_P12.png` mostram "1 Missing alternative text" em todas as páginas com o modal (B36), `WAVE_P09.png` mostra o campo "Buscar conversa" com o ícone de rótulo ausente (B39) `WAVE_P11.png` mostra o alerta de título de primeiro nível ausente (B40) e `WAVE_P06.png`, `WAVE_P10.png` e `WAVE_P12.png` mostram 1 erro de contraste que não pertence a nenhuma outra barreira (B41). Foram incluídas em 16/11/2026 e entram nos números da avaliação inicial.

## B33 e o item K1 do checklist

A B33 (os botões Perdido e Achado do modal Cadastrar item não recebem foco pelo teclado, porque os rádios estão com `display: none`) foi encontrada em 16/11/2026, durante a correção da B10, fora da rodada inicial. A inspeção por teclado da rodada "antes" não a identificou, e por isso o K1 ficou como "Atende". A B33 não entra nos números da avaliação inicial. A evidência `B33_antes.png` foi tirada na versão da tag `a11y-antes`.

## B34 e o item K8 do checklist

A B34 (os rádios do modal de filtros da `/menu/`, Todos, Perdido, Achado e Devolvido, não recebem foco pelo teclado, porque estão com `display: none`) foi encontrada em 16/11/2026, durante as correções, fora da rodada inicial. A inspeção por teclado da rodada "antes" não a identificou, e por isso o K8 ficou como "Atende" na P05. A B34 não entra nos números da avaliação inicial. A evidência `B34_antes.png` foi tirada na versão da tag `a11y-antes`.

## B35, B37 e B38

As barreiras B35 (select de categoria do modal de filtros sem rótulo), B37 (envio da foto de perfil na P11 sem acesso pelo teclado) e B38 (campo de arquivo escondido do modal Editar perfil) foram encontradas em 16/11/2026, durante as correções, fora da rodada inicial. Nenhuma ferramenta nem a inspeção da rodada "antes" as identificaram, e elas não entram nos números da avaliação inicial. Para a B35, foi feito um teste na versão da tag `a11y-antes`: com um `aria-label` temporário no select, o WAVE continuou mostrando 14 "Missing form label" na P05, ou seja, o select não era contado na rodada inicial. O teste foi desfeito.

## Achado fora da amostra

O campo de arquivo escondido de `item_edit.html:25` (troca da foto do item) tem o mesmo problema da B37, mas fica na página `/item/editar/`, que não faz parte das 12 páginas da amostra. Por isso não virou barreira.
