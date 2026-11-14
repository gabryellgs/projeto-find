import pytest

from correspondencia.estrategias import F
from items.models import Categoria, Item


@pytest.mark.django_db
def test_sem_foto_mesmo_texto_mesma_categoria_pontuacao_um():
    """Com usar_foto=False, mesmo texto e mesma categoria → pontuação final = 1."""
    categoria = Categoria.objects.create(nome="Acessórios")
    perdido = Item(titulo="Garrafa azul", descricao="marca Stanley", categoria=categoria, status="perdido")
    achado = Item(id=1, titulo="Garrafa azul", descricao="marca Stanley", categoria=categoria, status="achado")

    f = F(usar_foto=False)
    f.preparar([achado])
    pontuacoes = f.pontuar(perdido)

    # (0.6 * 1.0 + 0.1 * 1.0) / 0.7 = 1.0
    assert pontuacoes[1] == pytest.approx(1.0)


@pytest.mark.django_db
def test_sem_foto_categoria_diferente():
    """Com usar_foto=False e categorias diferentes, categoria vale 0."""
    cat_a = Categoria.objects.create(nome="Acessórios")
    cat_b = Categoria.objects.create(nome="Eletrônicos")
    perdido = Item(titulo="Garrafa azul", descricao="marca Stanley", categoria=cat_a, status="perdido")
    achado = Item(id=1, titulo="Garrafa azul", descricao="marca Stanley", categoria=cat_b, status="achado")

    f = F(usar_foto=False)
    f.preparar([achado])
    pontuacoes = f.pontuar(perdido)

    # (0.6 * 1.0 + 0.1 * 0.0) / 0.7 ≈ 0.857
    assert pontuacoes[1] == pytest.approx(0.857, abs=0.001)

