# Análise de erros

Esta seção documenta os casos em que a estratégia **V** (pHash + histograma de cor)
baixou a pontuação de pares corretos, e um caso em que a **F** ganhou pontos da **B0**.

## Contexto

A estratégia **F** acertou **todos** os 40 pares em 1º lugar
(Recall@1 = 1,000; veja `resultados/metricas.csv`). Isso acontece porque o peso do
texto (0,6) domina a pontuação: mesmo quando a foto não ajuda, o TF-IDF já basta para
colocar o achado correto no topo.

Por isso a análise de erros olha para **onde a parte da imagem (V) erra**, já que é
exatamente o que o texto não consegue resolver sozinho — e é o que a F teria de acertar
se o texto também falhasse.

## Os 5 piores casos da V

Foram escolhidos os 5 pares com menor pontuação da estratégia V
(`posicoes.csv` filtrado por `estrategia=V`, ordenado por `pontuacao_correto`).

| # | Perdido (id) | Variação | V | pHash | Hist | Causa provável |
|---|---|---|---|---|---|---|
| 1 | Fonte preto (1730) | sinonimo | 0,378 | 0,484 | 0,047 | Sinônimo + iluminação oposta (A=112, B=149) + tamanhos diferentes |
| 2 | Garrafa branca (1742) | sem_acento | 0,395 | 0,461 | 0,051 | Sem acento + fundo dominante diferente (A=138, B=113) |
| 3 | Rabicó preta (1769) | sinonimo | 0,400 | 0,523 | 0,195 | Sinônimo + foto B muito mais escura (A=130, B=72) |
| 4 | Pente rosa (1775) | nenhuma | 0,413 | 0,508 | 0,167 | Ângulo/fundo diferente (A=94, B=118) |
| 5 | Limmpador facial verde (1772) | erro_digitacao | 0,450 | 0,469 | 0,172 | Erro de digitação + tamanhos diferentes (450×800 vs 480×640) |

> Os valores de luminância (mean_L) são a média do canal L da imagem, de 0 (preto) a 255
> (branco). Diferenças grandes indicam iluminação distinta entre a foto A (de quem achou)
> e a foto B (do dono), exatamente como manda o protocolo da Tarefa 2.2.

### Leitura dos casos

**Causa 1 — pHash não reconhece o mesmo objeto em foto diferente.**
O pHash foi feito para achar a *mesma foto* redimensionada, não o *mesmo objeto*
fotografado de outro ângulo, com outra luz e outro fundo. Nos 5 casos a distância de
Hamming ficou entre 122 e 138 bits de 256 (nota de hash entre 0,46 e 0,52), ou seja,
quase o valor de um par aleatório (0,5). O pHash simplesmente não guarda informação
sobre o objeto, só sobre a estrutura global da imagem.

**Causa 2 — o histograma de cor é dominado pelo fundo.**
A interseção de histogramas HSV ficou entre 0,047 e 0,195 (1,0 seria paleta idêntica).
Como o objeto ocupa parte pequena do quadro e o fundo é diferente em cada foto, as
cores de fundo pesam mais que as cores do objeto. O caso 1730 é o mais extremo:
histograma 0,047 com a foto A escura e a B clara.

**Causa 3 — variações no texto não afetam a V, mas mostram o limite do conjunto.**
Os casos 1730, 1769 (sinônimo) e 1772 (erro de digitação) mostram que, quando o texto
também é prejudicado, a foto não compensa: a V sozinha não resolve nada. Só a combinação
F garantiu o 1º lugar mesmo assim.

## Caso em que a F ganha da B0

O plano pedia **1 caso em que a F acertou e a B0 errou**. Como a B0 também acertou
todos os 40 pares em 1º lugar (Recall@1 = 1,000), não há caso de erro absoluto da B0.
O que existe — e é o fenômeno que interessa — é a F **ganhar pontos da B0** nos casos
em que o texto do perdido tem erro de digitação. O maior ganho:

| Perdido (id) | Variação | B0 | F | Ganho |
|---|---|---|---|---|
| Garraffa azul (1739) | erro_digitacao | 0,690 | 0,765 | +0,075 |

- **Texto do perdido:** "Procuro garraffa azul. Detalhe: com tampa azul e gargalo prateado."
- **Texto do achado:** "Garrafa azul. Com tampa azul e gargalo prateado."
- **O que acontece:** a B0 compara palavras exatas; "garraffa" ≠ "garrafa", então a
  parte do título (até 40 pontos) cai. A T1 dentro da F compara *pedaços* de 3 a 5
  letras ("gar", "arr", "rfa", "aff"...); quase todos continuam iguais, então a pontuação
  cai pouco. A F herda esse ganho do TF-IDF e termina com 0,765 contra 0,690 da B0.

Esse é o ganho concreto que a combinação traz: **a F resiste a erros de digitação que
a B0 não perdoa**, mesmo sem a foto ajudar (a V nesse caso foi 0,457, quase aleatória).

## Conclusão para o texto

1. A V sozinha é frágil: depende de ângulo, luz e fundo, que o protocolo de fotografia
   deixa justamente diferentes entre A e B.
2. A F compensa isso com o peso 0,6 no texto: mesmo com a V perto do aleatório, o
   TF-IDF segura o par correto em 1º.
3. O ganho da F sobre a B0 está nos erros de digitação, que o TF-IDF absorve e a
   heurística de palavras exatas não.
4. Limitação honesta para o texto: como a B0 também fez Recall@1 = 1,000, a vantagem
   da F neste experimento é **quantitativa** (pontuação maior, mais margem de segurança),
   não de acerto. Um conjunto com distratores mais parecidos seria necessário para ver a
   F salvar um caso que a B0 perde de fato.
