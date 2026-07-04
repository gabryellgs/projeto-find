"""API views para o app de Internet das Coisas (IoT)."""
import logging
from datetime import timedelta
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from items.models import Item
from items.api.views import _item_to_dict, _get_client_ip
from iot.models import Dispositivo, LeituraLog

logger = logging.getLogger(__name__)

@api_view(["POST"])
@permission_classes([AllowAny])
def api_iot_scan(request):
    """
    Endpoint dedicado para receber leituras de módulos IoT (ESP32).
    Requer header: Authorization: Hardware-Token <token>
    Payload esperado: {"rfid_uid": "04 EA B1 22", "acao": "scan"}
    """
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Hardware-Token "):
        logger.warning(f"Tentativa de acesso IoT sem header correto. IP: {_get_client_ip(request)}")
        return Response({"ok": False, "detail": "Acesso negado. Formato de token inválido."}, status=403)
        
    token_str = auth_header.replace("Hardware-Token ", "").strip()
    
    # 1. Autenticação Baseada no Banco de Dados
    try:
        dispositivo = Dispositivo.objects.get(token_auth=token_str, is_ativo=True)
    except Dispositivo.DoesNotExist:
        logger.warning(f"Tentativa de acesso IoT com token não reconhecido: {token_str}. IP: {_get_client_ip(request)}")
        return Response({"ok": False, "detail": "Acesso negado. Dispositivo inativo ou token inválido."}, status=403)

    # Atualiza last_seen do dispositivo
    dispositivo.ultima_comunicacao = timezone.now()
    dispositivo.save(update_fields=["ultima_comunicacao"])

    # 2. Processamento do RFID
    rfid_uid = request.data.get("rfid_uid", "").strip()
    if not rfid_uid:
        return Response({"ok": False, "detail": "O campo 'rfid_uid' é obrigatório."}, status=400)

    try:
        item = Item.objects.select_related("usuario", "categoria").get(rfid_uid__iexact=rfid_uid)
        
        # Registra no log do IoT
        LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid=rfid_uid,
            sucesso_identificacao=True,
            item_associado=item
        )
        
        return Response({
            "ok": True,
            "detail": f"Item identificado pelo leitor {dispositivo.nome}.",
            "item": _item_to_dict(item, request)
        })
    except Item.DoesNotExist:
        # Registra no log como tag virgem/não associada
        LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid=rfid_uid,
            sucesso_identificacao=False
        )
        
        return Response({
            "ok": False,
            "detail": "Etiqueta lida mas não associada a nenhum item no sistema.",
            "rfid_uid": rfid_uid
        }, status=404)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_iot_latest_scan(request):
    """
    Retorna a leitura RFID mais recente dos últimos 15 segundos.
    Usado pelo frontend para auto-preencher o campo RFID no formulário
    de cadastro quando o operador coloca a tag no leitor físico.
    """
    janela = timezone.now() - timedelta(seconds=15)
    leitura = (
        LeituraLog.objects
        .filter(timestamp__gte=janela)
        .order_by("-timestamp")
        .first()
    )

    if not leitura:
        return Response({"ok": False, "rfid_uid": None})

    return Response({
        "ok": True,
        "rfid_uid": leitura.rfid_uid.upper(),
        "dispositivo": leitura.dispositivo.nome if leitura.dispositivo else "Desconhecido",
        "timestamp": leitura.timestamp.isoformat(),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def api_iot_scan(request):
    """
    Endpoint dedicado para receber leituras de módulos IoT (ESP32).
    Requer header: Authorization: Hardware-Token <token>
    Payload esperado: {"rfid_uid": "04 EA B1 22", "acao": "scan"}
    """
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Hardware-Token "):
        logger.warning(f"Tentativa de acesso IoT sem header correto. IP: {_get_client_ip(request)}")
        return Response({"ok": False, "detail": "Acesso negado. Formato de token inválido."}, status=403)
        
    token_str = auth_header.replace("Hardware-Token ", "").strip()
    
    # 1. Autenticação Baseada no Banco de Dados
    try:
        dispositivo = Dispositivo.objects.get(token_auth=token_str, is_ativo=True)
    except Dispositivo.DoesNotExist:
        logger.warning(f"Tentativa de acesso IoT com token não reconhecido: {token_str}. IP: {_get_client_ip(request)}")
        return Response({"ok": False, "detail": "Acesso negado. Dispositivo inativo ou token inválido."}, status=403)

    # Atualiza last_seen do dispositivo
    dispositivo.ultima_comunicacao = timezone.now()
    dispositivo.save(update_fields=["ultima_comunicacao"])

    # 2. Processamento do RFID
    rfid_uid = request.data.get("rfid_uid", "").strip()
    if not rfid_uid:
        return Response({"ok": False, "detail": "O campo 'rfid_uid' é obrigatório."}, status=400)

    try:
        item = Item.objects.select_related("usuario", "categoria").get(rfid_uid__iexact=rfid_uid)
        
        # Registra no log do IoT
        LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid=rfid_uid,
            sucesso_identificacao=True,
            item_associado=item
        )
        
        return Response({
            "ok": True,
            "detail": f"Item identificado pelo leitor {dispositivo.nome}.",
            "item": _item_to_dict(item, request)
        })
    except Item.DoesNotExist:
        # Registra no log como tag virgem/não associada
        LeituraLog.objects.create(
            dispositivo=dispositivo,
            rfid_uid=rfid_uid,
            sucesso_identificacao=False
        )
        
        return Response({
            "ok": False,
            "detail": "Etiqueta lida mas não associada a nenhum item no sistema.",
            "rfid_uid": rfid_uid
        }, status=404)
