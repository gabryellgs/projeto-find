import pytest

from correspondencia.estrategias import T1
from items.models import Categoria, Item


@pytest.mark.django_db
def test_achado_com_mesmo_texto_fica_em_primeiro():
    categoria = Categoria.objects.create(nome="Acessórios")
    perdido = Item(titulo="Garrafa azul", descricao="marca Stanley", categoria=categoria, status="perdido")
    achado_correto = Item(id=1, titulo="Garrafa azul", descricao="marca Stanley", categoria=categoria, status="achado")
    achado_outro = Item(id=2, titulo="Mochila preta", descricao="marca Nike", categoria=categoria, status="achado")

    t1 = T1()
    t1.preparar([achado_correto, achado_outro])
    pontuacoes = t1.pontuar(perdido)

    assert pontuacoes[1] > pontuacoes[2]


@pytest.mark.django_db
def test_t1_pontuacao_entre_zero_e_um():
    categoria = Categoria.objects.create(nome="Eletrônicos")
    perdido = Item(titulo="Carregador branco", descricao="USB-C", categoria=categoria, status="perdido")
    achado = Item(id=1, titulo="Fone preto", descricao="Sony", categoria=categoria, status="achado")

    t1 = T1()
    t1.preparar([achado])
    pontuacoes = t1.pontuar(perdido)

    assert 0 <= pontuacoes[1] <= 1

