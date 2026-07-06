"""Testes para os models do app IoT."""
import uuid
import pytest
from datetime import date

from django.contrib.auth.models import User
from django.utils import timezone

from iot.models import Dispositivo, LeituraLog
from items.models import Item


# ──────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────
@pytest.fixture
def dispositivo(db):
    """Cria um dispositivo (leitor RFID) de teste."""
    return Dispositivo.objects.create(
        nome="Leitor RFID COAPAC Balcão",
        token_auth="token-secreto-teste-1234",
        is_ativo=True,
    )


@pytest.fixture
def dispositivo_inativo(db):
    """Cria um dispositivo inativo para testes de autenticação."""
    return Dispositivo.objects.create(
        nome="Leitor RFID Inativo",
        token_auth="token-inativo-5678",
        is_ativo=False,
    )


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="iotuser",
        email="iot@example.com",
        password="Str0ngP@ss!",
    )


@pytest.fixture
def item(user):
    return Item.objects.create(
        titulo="Mochila Preta",
        descricao="Mochila de nylon preta",
        status="perdido",
        local="Biblioteca",
        data=date.today(),
        usuario=user,
        rfid_uid="04 EA B1 22",
    )


# ──────────────────────────────────────────────────────────────
# Dispositivo
# ──────────────────────────────────────────────────────────────
class TestDispositivoModel:
    """Testes para o model Dispositivo."""

    def test_criar_dispositivo(self, dispositivo):
        """Dispositivo deve ser criado com PK válida."""
        assert dispositivo.pk is not None

    def test_dispositivo_pk_e_uuid(self, dispositivo):
        """A chave primária deve ser um UUID."""
        assert isinstance(dispositivo.pk, uuid.UUID)

    def test_dispositivo_str_ativo(self, dispositivo):
        """__str__ deve indicar nome e status Ativo."""
        assert str(dispositivo) == "Leitor RFID COAPAC Balcão (Ativo)"

    def test_dispositivo_str_inativo(self, dispositivo_inativo):
        """__str__ deve indicar nome e status Inativo."""
        assert str(dispositivo_inativo) == "Leitor RFID Inativo (Inativo)"

    def test_dispositivo_is_ativo_por_padrao(self, db):
        """Novos dispositivos devem ser criados como ativos por padrão."""
        d = Dispositivo.objects.create(
            nome="Novo Leitor",
            token_auth="token-novo-9999",
        )
        assert d.is_ativo is True

    def test_dispositivo_ultima_comunicacao_nula(self, dispositivo):
        """ultima_comunicacao deve ser None ao criar o dispositivo."""
        assert dispositivo.ultima_comunicacao is None

    def test_dispositivo_atualizar_ultima_comunicacao(self, dispositivo):
        """Deve ser possível atualizar o campo ultima_comunicacao."""
        agora = timezone.now()
        dispositivo.ultima_comunicacao = agora
        dispositivo.save(update_fields=["ultima_comunicacao"])
        dispositivo.refresh_from_db()
        assert dispositivo.ultima_comunicacao is not None

    def test_dispositivo_token_unico(self, dispositivo, db):
        """Dois dispositivos não podem ter o mesmo token_auth."""
        with pytest.raises(Exception):
            Dispositivo.objects.create(
                nome="Outro Leitor",
                token_auth="token-secreto-teste-1234",  # duplicado
            )

    def test_dispositivo_criado_em_auto(self, dispositivo):
        """O campo criado_em deve ser preenchido automaticamente."""
        assert dispositivo.criado_em is not None

    def test_dispositivo_desativar(self, dispositivo):
        """Deve ser possível desativar um dispositivo."""
        dispositivo.is_ativo = False
        dispositivo.save(update_fields=["is_ativo"])
        dispositivo.refresh_from_db()
        assert dispositivo.is_ativo is False
        assert "Inativo" in str(dispositivo)


# ──────────────────────────────────────────────────────────────
# LeituraLog
# ──────────────────────────────────────────────────────────────
class TestLeituraLogModel:
    """Testes para o model LeituraLog."""

    def test_criar_leitura_log_com_sucesso(self, dispositivo, item):
        """Deve criar um log de leitura bem-sucedida com item associado."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid="04 EA B1 22",
            sucesso_identificacao=True,
            item_associado=item,
        )
        assert log.pk is not None
        assert log.sucesso_identificacao is True
        assert log.item_associado == item

    def test_criar_leitura_log_sem_item(self, dispositivo):
        """Deve criar um log de leitura de tag não identificada (sem item)."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid="FF AB 12 33",
            sucesso_identificacao=False,
        )
        assert log.pk is not None
        assert log.sucesso_identificacao is False
        assert log.item_associado is None

    def test_leitura_log_str(self, dispositivo):
        """__str__ deve conter a UID da tag e o nome do dispositivo."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid="AA BB CC DD",
            sucesso_identificacao=False,
        )
        resultado = str(log)
        assert "AA BB CC DD" in resultado
        assert "Leitor RFID COAPAC Balcão" in resultado

    def test_leitura_log_timestamp_auto(self, dispositivo):
        """O campo timestamp deve ser preenchido automaticamente."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid="00 11 22 33",
            sucesso_identificacao=False,
        )
        assert log.timestamp is not None

    def test_sucesso_identificacao_falso_por_padrao(self, dispositivo):
        """O campo sucesso_identificacao deve ser False por padrão."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid="99 88 77 66",
        )
        assert log.sucesso_identificacao is False

    def test_multiplas_leituras_por_dispositivo(self, dispositivo):
        """Um dispositivo pode ter múltiplos logs de leitura."""
        for i in range(5):
            LeituraLog.objects.create(
                dispositivo=dispositivo,
                rfid_uid=f"TAG-{i:04d}",
                sucesso_identificacao=False,
            )
        assert dispositivo.leituras.count() == 5

    def test_leitura_log_set_null_ao_deletar_dispositivo(self, dispositivo):
        """Ao deletar o dispositivo, o log deve manter o registro com dispositivo=None."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid="EE FF 00 11",
            sucesso_identificacao=False,
        )
        dispositivo.delete()
        log.refresh_from_db()
        assert log.dispositivo is None

    def test_leitura_log_set_null_ao_deletar_item(self, dispositivo, item):
        """Ao deletar o item, o log deve manter o registro com item_associado=None."""
        log = LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid=item.rfid_uid,
            sucesso_identificacao=True,
            item_associado=item,
        )
        item.delete()
        log.refresh_from_db()
        assert log.item_associado is None
