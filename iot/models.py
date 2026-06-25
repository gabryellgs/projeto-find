from django.db import models
import uuid

class Dispositivo(models.Model):
    """
    Representa um leitor de hardware físico (Ex: ESP32 na COPAC).
    Isso permite ter múltiplos leitores, cada um com sua senha e localidade.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100, help_text="Ex: Leitor RFID COPAC Balcão")
    token_auth = models.CharField(max_length=64, unique=True, help_text="Token secreto que este dispositivo usa para se autenticar")
    is_ativo = models.BooleanField(default=True)
    ultima_comunicacao = models.DateTimeField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({'Ativo' if self.is_ativo else 'Inativo'})"

class LeituraLog(models.Model):
    """
    Registra todas as leituras brutas que chegam de qualquer dispositivo,
    mesmo que a tag lida não esteja associada a nenhum item ainda.
    """
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.SET_NULL, null=True, related_name='leituras')
    rfid_uid = models.CharField(max_length=50)
    sucesso_identificacao = models.BooleanField(default=False, help_text="True se o sistema achou um Item para essa tag")
    item_associado = models.ForeignKey('items.Item', on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tag {self.rfid_uid} lida por {self.dispositivo} em {self.timestamp.strftime('%d/%m/%Y %H:%M')}"
