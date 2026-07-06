"""Testes para as views web do app mainpage."""
import pytest
from datetime import date

from django.contrib.auth.models import User
from django.test import Client

from accounts.models import Profile
from items.models import Categoria, Item
from chats.models import Chat, Mensagem


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="webuser",
        email="web@example.com",
        password="Str0ngP@ss!",
        first_name="Web",
        last_name="User",
    )
    Profile.objects.get_or_create(user=u)
    return u


@pytest.fixture
def other_user(db):
    u = User.objects.create_user(
        username="outrousuario",
        email="outro@example.com",
        password="Str0ngP@ss!",
    )
    Profile.objects.get_or_create(user=u)
    return u


@pytest.fixture
def auth_client(client, user):
    client.login(username="webuser", password="Str0ngP@ss!")
    return client


@pytest.fixture
def categoria(db):
    return Categoria.objects.create(nome="Documentos")


@pytest.fixture
def item(user, categoria):
    return Item.objects.create(
        titulo="RG Perdido",
        descricao="RG nome João",
        status="perdido",
        local="Shopping Rio Mar",
        data=date.today(),
        usuario=user,
        categoria=categoria,
    )


# ──────────────────────────────────────────────────────────────
# Home / Auth
# ──────────────────────────────────────────────────────────────
class TestHomeView:

    def test_home_status_200(self, client, db):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_home_contadores(self, client, item):
        resp = client.get("/")
        assert resp.status_code == 200


class TestLoginView:

    def test_get_login_page(self, client, db):
        resp = client.get("/login/")
        assert resp.status_code == 200

    def test_login_com_username(self, client, user):
        resp = client.post("/login/", {
            "username": "webuser",
            "password": "Str0ngP@ss!",
        })
        assert resp.status_code == 302  # redirect para menu
        assert resp.url == "/menu/" or "menu" in resp.url

    def test_login_com_email(self, client, user):
        resp = client.post("/login/", {
            "username": "web@example.com",
            "password": "Str0ngP@ss!",
        })
        assert resp.status_code == 302

    def test_login_credenciais_erradas(self, client, user):
        resp = client.post("/login/", {
            "username": "webuser",
            "password": "errada",
        })
        assert resp.status_code == 200  # fica na página de login


class TestLogoutView:

    def test_logout(self, auth_client):
        resp = auth_client.get("/logout/")
        assert resp.status_code == 302
        assert resp.url == "/login/" or "login" in resp.url


class TestRegisterView:

    def test_get_register_page(self, client, db):
        resp = client.get("/register/")
        assert resp.status_code == 200

    def test_registro_sucesso(self, client, db):
        resp = client.post("/register/", {
            "full_name": "Novo Usuário",
            "username": "novousuario",
            "email": "novo@example.com",
            "password": "Str0ngP@ss!",
            "confirm_password": "Str0ngP@ss!",
            "data_nascimento": "2000-01-01",
        })
        assert resp.status_code == 302
        assert User.objects.filter(username="novousuario").exists()

    def test_registro_senhas_diferentes(self, client, db):
        resp = client.post("/register/", {
            "full_name": "Teste",
            "username": "senhadif",
            "email": "senhadif@example.com",
            "password": "Str0ngP@ss!",
            "confirm_password": "OutraSenha123!",
        })
        assert resp.status_code == 302  # redirect com mensagem de erro
        assert not User.objects.filter(username="senhadif").exists()

    def test_registro_username_duplicado(self, client, user):
        resp = client.post("/register/", {
            "full_name": "Teste",
            "username": "webuser",
            "email": "outro@email.com",
            "password": "Str0ngP@ss!",
            "confirm_password": "Str0ngP@ss!",
        })
        assert resp.status_code == 302
        assert User.objects.filter(username="webuser").count() == 1

    def test_registro_email_duplicado(self, client, user):
        resp = client.post("/register/", {
            "full_name": "Teste",
            "username": "outrouser",
            "email": "web@example.com",
            "password": "Str0ngP@ss!",
            "confirm_password": "Str0ngP@ss!",
        })
        assert resp.status_code == 302
        assert not User.objects.filter(username="outrouser").exists()

    def test_registro_menor_13_anos(self, client, db):
        resp = client.post("/register/", {
            "full_name": "Criança",
            "username": "crianca",
            "email": "crianca@example.com",
            "password": "Str0ngP@ss!",
            "confirm_password": "Str0ngP@ss!",
            "data_nascimento": "2020-01-01",
        })
        assert resp.status_code == 302
        assert not User.objects.filter(username="crianca").exists()


# ──────────────────────────────────────────────────────────────
# Menu / Páginas autenticadas
# ──────────────────────────────────────────────────────────────
class TestMenuView:

    def test_menu_autenticado(self, auth_client, item):
        resp = auth_client.get("/menu/")
        assert resp.status_code == 200

    def test_menu_nao_autenticado_redireciona(self, client, db):
        resp = client.get("/menu/")
        assert resp.status_code == 302
        assert "login" in resp.url


class TestScreenUserView:

    def test_tela_usuario_autenticado(self, auth_client, item):
        resp = auth_client.get("/tela/")
        assert resp.status_code == 200

    def test_tela_nao_autenticado_redireciona(self, client, db):
        resp = client.get("/tela/")
        assert resp.status_code == 302


# ──────────────────────────────────────────────────────────────
# CRUD de itens (web)
# ──────────────────────────────────────────────────────────────
class TestRegisterItemView:

    def test_cadastrar_item(self, auth_client, categoria):
        resp = auth_client.post("/perfil/item/novo/", {
            "titulo": "Carteira Azul",
            "descricao": "Carteira de couro azul",
            "categoria": categoria.id,
            "status": "perdido",
            "data": str(date.today()),
            "local": "Ônibus 101",
        })
        assert resp.status_code == 302
        assert Item.objects.filter(titulo="Carteira Azul").exists()

    def test_cadastrar_item_titulo_curto(self, auth_client, categoria):
        resp = auth_client.post("/perfil/item/novo/", {
            "titulo": "AB",
            "descricao": "desc",
            "categoria": categoria.id,
            "status": "perdido",
            "data": str(date.today()),
            "local": "Local",
        })
        assert resp.status_code == 302
        assert not Item.objects.filter(titulo="AB").exists()


class TestEditItemView:

    def test_editar_item_proprio(self, auth_client, item):
        resp = auth_client.post(f"/item/editar/{item.id}/", {
            "titulo": "RG Atualizado",
            "descricao": item.descricao,
            "local": item.local,
            "status": item.status,
            "data": str(item.data),
        })
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.titulo == "RG Atualizado"

    def test_editar_item_de_outro_retorna_404(self, auth_client, other_user, categoria):
        item_outro = Item.objects.create(
            titulo="Item Outro",
            descricao="desc",
            status="perdido",
            local="Local",
            data=date.today(),
            usuario=other_user,
            categoria=categoria,
        )
        resp = auth_client.get(f"/item/editar/{item_outro.id}/")
        assert resp.status_code == 404


class TestDeleteItemView:

    def test_deletar_item_proprio(self, auth_client, item):
        resp = auth_client.post(f"/item/deletar/{item.id}/")
        assert resp.status_code == 302
        assert not Item.objects.filter(id=item.id).exists()

    def test_deletar_item_de_outro_retorna_404(self, auth_client, other_user):
        item_outro = Item.objects.create(
            titulo="Item Outro",
            descricao="desc",
            status="perdido",
            local="Local",
            data=date.today(),
            usuario=other_user,
        )
        resp = auth_client.post(f"/item/deletar/{item_outro.id}/")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Listagens de itens
# ──────────────────────────────────────────────────────────────
class TestItemListViews:

    def test_list_item(self, auth_client, item):
        resp = auth_client.get("/itens/")
        assert resp.status_code == 200

    def test_items_perdidos(self, auth_client, item):
        resp = auth_client.get("/itens/perdidos/")
        assert resp.status_code == 200

    def test_items_encontrados(self, auth_client, item):
        item.status = "achado"
        item.save(update_fields=["status"])
        resp = auth_client.get("/itens/encontrados/")
        assert resp.status_code == 200

    def test_items_devolvidos(self, auth_client, item):
        item.status = "devolvido"
        item.save(update_fields=["status"])
        resp = auth_client.get("/itens/devolvidos/")
        assert resp.status_code == 200

    def test_meus_itens(self, auth_client, item):
        resp = auth_client.get("/meus-itens/")
        assert resp.status_code == 200

    def test_itens_recentes(self, auth_client, item):
        resp = auth_client.get("/itens/recentes/")
        assert resp.status_code == 200


# ──────────────────────────────────────────────────────────────
# Detalhe do item
# ──────────────────────────────────────────────────────────────
class TestItemDetailView:

    def test_item_detail_por_slug(self, client, item):
        resp = client.get(f"/item/{item.slug}/")
        assert resp.status_code == 200

    def test_item_detail_slug_inexistente(self, client, db):
        resp = client.get("/item/slug-inexistente/")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Marcar status
# ──────────────────────────────────────────────────────────────
class TestMarcarStatusViews:

    def test_marcar_devolvido(self, auth_client, item):
        resp = auth_client.post(f"/itens/{item.id}/devolver/")
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.status == "devolvido"

    def test_marcar_achado(self, auth_client, item):
        resp = auth_client.post(f"/itens/{item.id}/achado/")
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.status == "achado"

    def test_marcar_perdido(self, auth_client, item):
        item.status = "achado"
        item.save(update_fields=["status"])
        resp = auth_client.post(f"/itens/{item.id}/perdido/")
        assert resp.status_code == 302
        item.refresh_from_db()
        assert item.status == "perdido"

    def test_marcar_devolvido_item_de_outro_retorna_404(self, auth_client, other_user):
        item_outro = Item.objects.create(
            titulo="Item Outro",
            descricao="desc",
            status="perdido",
            local="Local",
            data=date.today(),
            usuario=other_user,
        )
        resp = auth_client.post(f"/itens/{item_outro.id}/devolver/")
        assert resp.status_code == 404


# ──────────────────────────────────────────────────────────────
# Sugestões de busca
# ──────────────────────────────────────────────────────────────
class TestSearchSuggestions:

    def test_suggestions_retorna_json(self, auth_client, item):
        resp = auth_client.get("/menu/suggestions/?q=RG")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_suggestions_sem_query(self, auth_client, db):
        resp = auth_client.get("/menu/suggestions/")
        assert resp.status_code == 200
        assert resp.json() == []


# ──────────────────────────────────────────────────────────────
# Chat views (web)
# ──────────────────────────────────────────────────────────────
class TestChatWebViews:

    def test_iniciar_chat(self, auth_client, other_user):
        item_outro = Item.objects.create(
            titulo="Item do Outro",
            descricao="desc",
            status="achado",
            local="Local",
            data=date.today(),
            usuario=other_user,
        )
        resp = auth_client.get(f"/chats/iniciar/{item_outro.id}/")
        assert resp.status_code == 302
        assert Chat.objects.filter(item=item_outro).exists()

    def test_nao_inicia_chat_consigo_mesmo(self, auth_client, item):
        resp = auth_client.get(f"/chats/iniciar/{item.id}/")
        assert resp.status_code == 302
        assert not Chat.objects.filter(item=item, criado_por=item.usuario).exists()

    def test_chats_list_autenticado(self, auth_client, db):
        resp = auth_client.get("/chats/")
        assert resp.status_code == 200

    def test_enviar_mensagem_ajax(self, auth_client, user, other_user):
        item_outro = Item.objects.create(
            titulo="Item Chat",
            descricao="desc",
            status="achado",
            local="Local",
            data=date.today(),
            usuario=other_user,
        )
        chat = Chat.objects.create(
            item=item_outro,
            criado_por=user,
            dono_item=other_user,
            status="ativo",
        )
        resp = auth_client.post(f"/chats/{chat.id}/enviar/", {"conteudo": "Olá!"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

    def test_fechar_chat_apenas_dono_item(self, auth_client, user, other_user):
        """Apenas o dono do item pode fechar o chat."""
        item_outro = Item.objects.create(
            titulo="Item Fechar",
            descricao="desc",
            status="achado",
            local="Local",
            data=date.today(),
            usuario=other_user,
        )
        chat = Chat.objects.create(
            item=item_outro,
            criado_por=user,
            dono_item=other_user,
            status="ativo",
        )
        # user (criado_por) tenta fechar — não é o dono
        resp = auth_client.post(f"/chats/{chat.id}/fechar/")
        assert resp.status_code == 302
        chat.refresh_from_db()
        assert chat.status == "ativo"  # não fechou


# ──────────────────────────────────────────────────────────────
# Perfil (web)
# ──────────────────────────────────────────────────────────────
class TestUpdateProfileView:

    def test_atualizar_perfil(self, auth_client, user):
        # A view (mainpage/views.py::update_profile) e o formulário real
        # (edit_profile.html) usam o campo "first_name", não "nome".
        resp = auth_client.post("/perfil/atualizar/", {
            "first_name": "NomeNovo",
            "telefone": "(85) 99999-1111",
            "cidade": "Fortaleza",
            "estado": "CE",
            "cep": "60000-000",
        })
        assert resp.status_code == 302
        user.refresh_from_db()
        assert user.first_name == "NomeNovo"
        profile = Profile.objects.get(user=user)
        assert profile.cidade == "Fortaleza"
