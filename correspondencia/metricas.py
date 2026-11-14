def recall_em_k(posicoes, k):
    return sum(1 for p in posicoes if p <= k) / len(posicoes)


def mrr(posicoes):
    return sum(1 / p for p in posicoes) / len(posicoes)


def posicao_do_correto(pontuacoes, id_correto):
    """Ordena da maior para a menor pontuação; em empate, pelo menor id."""
    ordem = sorted(pontuacoes, key=lambda id_: (-pontuacoes[id_], id_))
    return ordem.index(id_correto) + 1

