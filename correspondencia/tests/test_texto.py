from correspondencia.texto import normalizar


def test_normalizar_remove_acentos_pontuacao_e_stopwords():
    assert normalizar("Óculos de sol, pretos!") == "oculos sol pretos"


def test_normalizar_texto_sem_acento():
    assert normalizar("garrafa azul grande") == "garrafa azul grande"


def test_normalizar_texto_vazio():
    assert normalizar("") == ""

