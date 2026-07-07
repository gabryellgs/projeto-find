"""Testes para os models do app items."""
import pytest
from datetime import date

from django.contrib.auth.models import User

from items.models import Categoria, Item, ArquivoMidia


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="itemuser",
        email="item@example.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nome="Eletrônicos", descricao="Dispositivos")


@pytest.fixture
def item(user, categoria):
    return Item.objects.create(
        titulo="Celular Samsung",
        descricao="Galaxy S24 preto",
        status="perdido",
        local="Shopping Iguatemi",
        data=date.today(),
        usuario=user,
        categoria=categoria,
    )


# ──────────────────────────────────────────────────────────────
# Categoria
# ──────────────────────────────────────────────────────────────
class TestCategoriaModel:

    def test_criar_categoria(self, categoria):
        assert categoria.pk is not None
        assert categoria.nome == "Eletrônicos"

    def test_categoria_str(self, categoria):
        assert str(categoria) == "Eletrônicos"

    def test_categoria_descricao_opcional(self, db):
        cat = Categoria.objects.create(nome="Documentos")
        assert cat.descricao == ""


# ──────────────────────────────────────────────────────────────
# ArquivoMidia
# ──────────────────────────────────────────────────────────────
class TestArquivoMidiaModel:

    def test_criar_arquivo_midia(self, db):
        arq = ArquivoMidia.objects.create(
            nome="foto_teste.jpg",
            conteudo=b"\x89PNG\r\n\x1a\n",
            content_type="image/jpeg",
            tamanho=1024,
        )
        assert arq.pk is not None
        assert str(arq) == "foto_teste.jpg"

    def test_nome_unico(self, db):
        ArquivoMidia.objects.create(nome="unico.jpg", conteudo=b"data")
        with pytest.raises(Exception):
            ArquivoMidia.objects.create(nome="unico.jpg", conteudo=b"data2")

    def test_content_type_padrao(self, db):
        arq = ArquivoMidia.objects.create(nome="sem_type.jpg", conteudo=b"data")
        assert arq.content_type == "image/jpeg"


# ──────────────────────────────────────────────────────────────
# Item
# ──────────────────────────────────────────────────────────────
class TestItemModel:

    def test_criar_item(self, item):
        assert item.pk is not None
        assert item.titulo == "Celular Samsung"
        assert item.status == "perdido"

    def test_item_str(self, item):
        assert str(item) == "Celular Samsung"

    def test_slug_gerado_automaticamente(self, item):
        # O model sempre acrescenta um sufixo aleatório ao slug para garantir unicidade.
        assert item.slug.startswith("celular-samsung-")
        assert len(item.slug) == len("celular-samsung-") + 6

    def test_slug_unico_para_titulo_repetido(self, user, categoria):
        """Itens com mesmo título devem gerar slugs diferentes."""
        item1 = Item.objects.create(
            titulo="Mochila Preta",
            descricao="Mochila de nylon",
            status="perdido",
            local="Praça",
            data=date.today(),
            usuario=user,
            categoria=categoria,
        )
        item2 = Item.objects.create(
            titulo="Mochila Preta",
            descricao="Outra mochila",
            status="achado",
            local="Terminal",
            data=date.today(),
            usuario=user,
            categoria=categoria,
        )
        assert item1.slug != item2.slug
        assert item2.slug.startswith("mochila-preta-")

    def test_status_choices_validos(self, item):
        valid_statuses = ["achado", "perdido", "devolvido"]
        for status in valid_statuses:
            item.status = status
            item.save(update_fields=["status"])
            item.refresh_from_db()
            assert item.status == status

    def test_item_pertence_ao_usuario(self, item, user):
        assert item.usuario == user
        assert item in user.itens.all()

    def test_item_com_categoria(self, item, categoria):
        assert item.categoria == categoria

    def test_item_sem_categoria(self, user):
        item = Item.objects.create(
            titulo="Item Sem Cat",
            descricao="desc",
            status="perdido",
            local="Local",
            data=date.today(),
            usuario=user,
            categoria=None,
        )
        assert item.categoria is None

    def test_item_categoria_set_null(self, item, categoria):
        """Quando a categoria é deletada, o item deve manter categoria=NULL."""
        categoria.delete()
        item.refresh_from_db()
        assert item.categoria is None

    def test_item_deletado_com_usuario(self, item, user):
        """Itens devem ser deletados quando o usuário for deletado (CASCADE)."""
        item_id = item.id
        user.delete()
        assert not Item.objects.filter(id=item_id).exists()

    def test_criado_em_auto(self, item):
        assert item.criado_em is not None

    def test_atualizado_em_auto(self, item):
        assert item.atualizado_em is not None

    def test_item_sem_imagem(self, item):
        assert not item.imagem

    def test_item_image_hash_vazio_sem_imagem(self, item):
        """Sem imagem, image_hash deve permanecer vazio."""
        assert not item.image_hash
