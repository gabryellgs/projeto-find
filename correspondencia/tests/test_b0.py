import pytest

from correspondencia.estrategias import B0
from items.models import Categoria, Item


@pytest.mark.django_db
def test_mesma_categoria_mesmo_titulo_descricoes_diferentes():
    # categoria 35 + título 2/2 palavras (40) + descrição 0 = 75
    categoria = Categoria.objects.create(nome="Acessórios")
    perdido = Item(titulo="Garrafa azul", descricao="perdi ontem", categoria=categoria, status="perdido")
    achado = Item(id=1, titulo="Garrafa azul", descricao="encontrada na cantina", categoria=categoria, status="achado")

    b0 = B0()
    b0.preparar([achado])

    assert b0.pontuar(perdido)[1] == pytest.approx(0.75)


@pytest.mark.django_db
def test_categorias_diferentes_e_metade_das_palavras_em_comum():
    # categoria 0 + título 1/2 (20) + descrição 1/2 (12,5) = 32,5 -> floor = 32
    cat_a = Categoria.objects.create(nome="Acessórios")
    cat_b = Categoria.objects.create(nome="Eletrônicos")
    perdido = Item(titulo="Garrafa azul", descricao="Stanley com adesivo", categoria=cat_a, status="perdido")
    achado = Item(id=2, titulo="Garrafa verde", descricao="Stanley sem tampa", categoria=cat_b, status="achado")

    b0 = B0()
    b0.preparar([achado])

    assert b0.pontuar(perdido)[2] == pytest.approx(0.32)


@pytest.mark.django_db
def test_acento_diferente_conta_como_palavra_diferente():
    # categoria 35 + título 1/2 (20; "óculos" != "oculos") + descrições vazias 0 = 55
    categoria = Categoria.objects.create(nome="Acessórios")
    perdido = Item(titulo="Óculos preto", descricao="", categoria=categoria, status="perdido")
    achado = Item(id=3, titulo="Oculos preto", descricao="", categoria=categoria, status="achado")

    b0 = B0()
    b0.preparar([achado])

    assert b0.pontuar(perdido)[3] == pytest.approx(0.55)