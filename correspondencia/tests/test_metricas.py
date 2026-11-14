import pytest

from correspondencia.metricas import mrr, posicao_do_correto, recall_em_k


def test_metricas_com_exemplo_calculado_a_mao():
    posicoes = [1, 2, 4]
    assert recall_em_k(posicoes, 1) == pytest.approx(1 / 3)
    assert recall_em_k(posicoes, 6) == 1
    assert mrr(posicoes) == pytest.approx(0.5833, abs=0.001)


def test_recall_em_k_nenhum_acerto():
    posicoes = [7, 10, 20]
    assert recall_em_k(posicoes, 6) == 0


def test_posicao_do_correto_desempate_por_id():
    pontuacoes = {10: 0.5, 20: 0.5, 30: 0.5}
    # Em empate, o menor id fica primeiro.
    assert posicao_do_correto(pontuacoes, 10) == 1
    assert posicao_do_correto(pontuacoes, 20) == 2
    assert posicao_do_correto(pontuacoes, 30) == 3

