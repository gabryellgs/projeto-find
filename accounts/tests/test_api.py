"""Testes para a API REST do app accounts."""
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from accounts.models import Profile


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="apiuser",
        email="api@example.com",
        password="Str0ngP@ss!",
        first_name="API",
        last_name="User",
    )
    Profile.objects.get_or_create(user=u)
    return u


@pytest.fixture
def auth_client(api_client, user):
    """Retorna um APIClient autenticado via JWT."""
    resp = api_client.post("/api/token/", {"username": "apiuser", "password": "Str0ngP@ss!"})
    assert resp.status_code == 200, resp.data
    token = resp.data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return api_client


# ──────────────────────────────────────────────────────────────
# Registro
# ──────────────────────────────────────────────────────────────
class TestApiRegister:

    def test_registro_sucesso(self, api_client, db):
        resp = api_client.post("/api/register/", {
            "username": "novouser",
            "email": "novo@email.com",
            "password": "Senh@Fort3!",
            "full_name": "Novo Usuário",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert "access" in resp.data["tokens"]
        assert User.objects.filter(username="novouser").exists()

    def test_registro_sem_username(self, api_client, db):
        resp = api_client.post("/api/register/", {
            "username": "",
            "password": "Senh@Fort3!",
        }, format="json")
        assert resp.status_code == 400
        assert resp.data["ok"] is False

    def test_registro_senha_curta(self, api_client, db):
        resp = api_client.post("/api/register/", {
            "username": "curto",
            "password": "123",
        }, format="json")
        assert resp.status_code == 400

    def test_registro_username_duplicado(self, api_client, user):
        resp = api_client.post("/api/register/", {
            "username": "apiuser",
            "password": "Senh@Fort3!",
        }, format="json")
        assert resp.status_code == 400
        assert "já está em uso" in resp.data["detail"] or "Username" in resp.data["detail"]

    def test_registro_email_duplicado(self, api_client, user):
        resp = api_client.post("/api/register/", {
            "username": "outrouser",
            "email": "api@example.com",
            "password": "Senh@Fort3!",
        }, format="json")
        assert resp.status_code == 400

    def test_registro_com_data_nascimento(self, api_client, db):
        resp = api_client.post("/api/register/", {
            "username": "comdata",
            "email": "comdata@email.com",
            "password": "Senh@Fort3!",
            "data_nascimento": "2000-01-15",
        }, format="json")
        assert resp.status_code == 200
        profile = Profile.objects.get(user__username="comdata")
        assert str(profile.data_nascimento) == "2000-01-15"


# ──────────────────────────────────────────────────────────────
# Token JWT
# ──────────────────────────────────────────────────────────────
class TestJwtToken:

    def test_obter_token_valido(self, api_client, user):
        resp = api_client.post("/api/token/", {
            "username": "apiuser",
            "password": "Str0ngP@ss!",
        })
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_token_senha_errada(self, api_client, user):
        resp = api_client.post("/api/token/", {
            "username": "apiuser",
            "password": "errada",
        })
        assert resp.status_code == 401

    def test_refresh_token(self, api_client, user):
        resp = api_client.post("/api/token/", {
            "username": "apiuser",
            "password": "Str0ngP@ss!",
        })
        refresh = resp.data["refresh"]
        resp2 = api_client.post("/api/token/refresh/", {"refresh": refresh})
        assert resp2.status_code == 200
        assert "access" in resp2.data


# ──────────────────────────────────────────────────────────────
# Perfil
# ──────────────────────────────────────────────────────────────
class TestApiProfile:

    def test_perfil_autenticado(self, auth_client):
        resp = auth_client.get("/api/profile/")
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert resp.data["data"]["username"] == "apiuser"

    def test_perfil_nao_autenticado(self, api_client, db):
        resp = api_client.get("/api/profile/")
        assert resp.status_code == 401

    def test_atualizar_perfil(self, auth_client, user):
        resp = auth_client.patch("/api/profile/update/", {
            "telefone": "(85) 98888-0000",
            "cidade": "Fortaleza",
            "estado": "CE",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["telefone"] == "(85) 98888-0000"
        assert resp.data["data"]["cidade"] == "Fortaleza"

    def test_atualizar_nome_completo(self, auth_client, user):
        resp = auth_client.patch("/api/profile/update/", {
            "full_name": "Novo Nome Completo",
        }, format="json")
        assert resp.status_code == 200
        assert resp.data["data"]["full_name"] == "Novo Nome Completo"

    def test_atualizar_username_duplicado(self, auth_client, db):
        User.objects.create_user(username="existente", password="Senh@123!")
        resp = auth_client.patch("/api/profile/update/", {
            "username": "existente",
        }, format="json")
        assert resp.status_code == 400

    def test_photo_sizes_endpoint(self, api_client, db):
        resp = api_client.get("/api/profile/photo-sizes/")
        assert resp.status_code == 200
        assert resp.data["ok"] is True
        assert "pequeno" in resp.data["data"]
        assert "grande" in resp.data["data"]


# ──────────────────────────────────────────────────────────────
# Admin: gestão de bolsistas
# ──────────────────────────────────────────────────────────────
class TestApiAdminBolsistasRemover:

    @pytest.fixture
    def admin_client(self, api_client, db):
        from django.contrib.auth.models import Group

        admin = User.objects.create_user(username="admin1", password="Str0ngP@ss!", is_staff=True)
        resp = api_client.post("/api/token/", {"username": "admin1", "password": "Str0ngP@ss!"})
        assert resp.status_code == 200, resp.data
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.data['access']}")
        return api_client

    def test_remover_bolsista_existente(self, admin_client, user):
        from django.contrib.auth.models import Group

        grupo, _ = Group.objects.get_or_create(name="Bolsistas")
        user.groups.add(grupo)

        resp = admin_client.delete(f"/api/admin/bolsistas/{user.id}/remover/")

        assert resp.status_code == 200
        assert resp.data["ok"] is True
        user.refresh_from_db()
        assert not user.groups.filter(name="Bolsistas").exists()

    def test_remover_usuario_inexistente_retorna_404(self, admin_client):
        resp = admin_client.delete("/api/admin/bolsistas/999999/remover/")
        assert resp.status_code == 404
