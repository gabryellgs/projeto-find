"""Testes para a API REST do app IoT (endpoint de scan RFID)."""
import pytest
from datetime import date

from django.contrib.auth.models import User
from rest_framework.test import APIClient

from iot.models import Dispositivo, LeituraLog
from items.models import Item


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def dispositivo(db):
    """Dispositivo ativo com token válido."""
    return Dispositivo.objects.create(
        nome="Leitor RFID COPAC",
        token_auth="token-valido-iot-9876",
        is_ativo=True,
    )


@pytest.fixture
def dispositivo_inativo(db):
    """Dispositivo inativo — não deve ser aceito pela API."""
    return Dispositivo.objects.create(
        nome="Leitor RFID Inativo",
        token_auth="token-inativo-iot-0001",
        is_ativo=False,
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="iotapiuser",
        email="iotapi@example.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def item_com_rfid(user):
    """Item com tag RFID cadastrada no sistema."""
    return Item.objects.create(
        titulo="Notebook Dell",
        descricao="Notebook prateado 15 polegadas",
        status="perdido",
        local="Biblioteca",
        data=date.today(),
        usuario=user,
        rfid_uid="04 EA B1 22",
    )


def _auth_header(token):
    """Helper: monta o header de autenticação Hardware-Token."""
    return {"HTTP_AUTHORIZATION": f"Hardware-Token {token}"}


# ──────────────────────────────────────────────────────────────
# Autenticação do dispositivo
# ──────────────────────────────────────────────────────────────
class TestIotScanAutenticacao:
    """Testes de autenticação do endpoint /api/iot/scan/."""

    def test_sem_header_authorization_retorna_403(self, api_client, db):
        resp = api_client.post("/api/iot/scan/", {"rfid_uid": "04 EA B1 22"}, format="json")
        assert resp.status_code == 403
        assert resp.data["ok"] is False

    def test_header_formato_errado_retorna_403(self, api_client, db):
        """Header com prefixo Bearer (não Hardware-Token) deve ser rejeitado."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer token-errado")
        resp = api_client.post("/api/iot/scan/", {"rfid_uid": "04 EA B1 22"}, format="json")
        assert resp.status_code == 403
        assert resp.data["ok"] is False

    def test_token_invalido_retorna_403(self, api_client, db):
        """Token inexistente no banco deve retornar 403."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "04 EA B1 22"},
            format="json",
            **_auth_header("token-que-nao-existe"),
        )
        assert resp.status_code == 403
        assert resp.data["ok"] is False

    def test_dispositivo_inativo_retorna_403(self, api_client, dispositivo_inativo):
        """Dispositivo com is_ativo=False deve ser rejeitado."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "04 EA B1 22"},
            format="json",
            **_auth_header(dispositivo_inativo.token_auth),
        )
        assert resp.status_code == 403
        assert resp.data["ok"] is False

    def test_token_valido_dispositivo_ativo_aceito(self, api_client, dispositivo, item_com_rfid):
        """Token válido com dispositivo ativo deve ser autenticado com sucesso."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        # 200 = item identificado; 404 = tag não associada — ambos são autenticados
        assert resp.status_code in (200, 404)


# ──────────────────────────────────────────────────────────────
# Scan com item identificado
# ──────────────────────────────────────────────────────────────
class TestIotScanItemIdentificado:
    """Testes do endpoint quando o RFID corresponde a um item cadastrado."""

    def test_scan_item_existente_retorna_200(self, api_client, dispositivo, item_com_rfid):
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True

    def test_scan_retorna_dados_do_item(self, api_client, dispositivo, item_com_rfid):
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 200
        assert "item" in resp.data
        assert resp.data["item"]["titulo"] == "Notebook Dell"

    def test_scan_cria_leitura_log_com_sucesso(self, api_client, dispositivo, item_com_rfid):
        """Uma leitura bem-sucedida deve gerar um LeituraLog com sucesso_identificacao=True."""
        api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert LeituraLog.objects.filter(
            dispositivo=dispositivo,
            rfid_uid=item_com_rfid.rfid_uid,
            sucesso_identificacao=True,
        ).exists()

    def test_scan_leitura_log_tem_item_associado(self, api_client, dispositivo, item_com_rfid):
        """O LeituraLog deve referenciar o item correto."""
        api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        log = LeituraLog.objects.get(
            dispositivo=dispositivo,
            rfid_uid=item_com_rfid.rfid_uid,
        )
        assert log.item_associado == item_com_rfid

    def test_scan_atualiza_ultima_comunicacao_dispositivo(self, api_client, dispositivo, item_com_rfid):
        """Após o scan, ultima_comunicacao do dispositivo deve ser atualizado."""
        assert dispositivo.ultima_comunicacao is None
        api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        dispositivo.refresh_from_db()
        assert dispositivo.ultima_comunicacao is not None

    def test_scan_rfid_case_insensitive(self, api_client, dispositivo, item_com_rfid):
        """O scan deve funcionar independentemente de maiúsculas/minúsculas no RFID."""
        rfid_lower = item_com_rfid.rfid_uid.lower()
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": rfid_lower},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 200
        assert resp.data["ok"] is True

    def test_scan_detail_contem_nome_dispositivo(self, api_client, dispositivo, item_com_rfid):
        """A mensagem 'detail' deve conter o nome do dispositivo."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": item_com_rfid.rfid_uid},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 200
        assert "Leitor RFID COPAC" in resp.data["detail"]


# ──────────────────────────────────────────────────────────────
# Scan com tag não identificada
# ──────────────────────────────────────────────────────────────
class TestIotScanTagNaoIdentificada:
    """Testes do endpoint quando a tag RFID não está associada a nenhum item."""

    def test_scan_rfid_desconhecido_retorna_404(self, api_client, dispositivo):
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "FF FF FF FF"},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 404
        assert resp.data["ok"] is False

    def test_scan_rfid_desconhecido_retorna_uid(self, api_client, dispositivo):
        """A resposta deve incluir o rfid_uid lido para rastreamento."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "FF FF FF FF"},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 404
        assert resp.data["rfid_uid"] == "FF FF FF FF"

    def test_scan_rfid_desconhecido_cria_log_sem_sucesso(self, api_client, dispositivo):
        """Tag não identificada deve gerar LeituraLog com sucesso_identificacao=False."""
        api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "CC DD EE FF"},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert LeituraLog.objects.filter(
            dispositivo=dispositivo,
            rfid_uid="CC DD EE FF",
            sucesso_identificacao=False,
        ).exists()

    def test_scan_rfid_desconhecido_log_sem_item_associado(self, api_client, dispositivo):
        """Log de tag desconhecida não deve ter item_associado."""
        api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "AA BB CC DD"},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        log = LeituraLog.objects.get(dispositivo=dispositivo, rfid_uid="AA BB CC DD")
        assert log.item_associado is None


# ──────────────────────────────────────────────────────────────
# Validação de payload
# ──────────────────────────────────────────────────────────────
class TestIotScanValidacaoPayload:
    """Testes de validação do corpo da requisição."""

    def test_sem_rfid_uid_retorna_400(self, api_client, dispositivo):
        """Requisição sem o campo rfid_uid deve retornar 400."""
        resp = api_client.post(
            "/api/iot/scan/",
            {},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 400
        assert resp.data["ok"] is False

    def test_rfid_uid_vazio_retorna_400(self, api_client, dispositivo):
        """Campo rfid_uid vazio (string vazia) deve retornar 400."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": ""},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 400
        assert resp.data["ok"] is False

    def test_rfid_uid_apenas_espacos_retorna_400(self, api_client, dispositivo):
        """Campo rfid_uid somente com espaços deve retornar 400 (strip)."""
        resp = api_client.post(
            "/api/iot/scan/",
            {"rfid_uid": "   "},
            format="json",
            **_auth_header(dispositivo.token_auth),
        )
        assert resp.status_code == 400
        assert resp.data["ok"] is False

    def test_multiplos_scans_geram_multiplos_logs(self, api_client, dispositivo):
        """Cada chamada ao endpoint deve gerar um novo LeituraLog."""
        for i in range(3):
            api_client.post(
                "/api/iot/scan/",
                {"rfid_uid": f"TAG {i:04d}"},
                format="json",
                **_auth_header(dispositivo.token_auth),
            )
        assert LeituraLog.objects.filter(dispositivo=dispositivo).count() == 3
