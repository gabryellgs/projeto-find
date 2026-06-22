"""API views para itens e categorias."""
import datetime
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from items.models import Item, Categoria
from accounts.permissoes import IsBolsistaOuAdmin


def _item_to_dict(item, request=None):
    imagem_url = None
    if item.imagem:
        if request:
            imagem_url = request.build_absolute_uri(item.imagem.url)
        else:
            imagem_url = item.imagem.url
    return {
        "id": item.id,
        "titulo": item.titulo,
        "descricao": item.descricao,
        "local": item.local,
        "status": item.status,
        "status_display": item.get_status_display(),
        "data": str(item.data) if item.data else "",
        "imagem": imagem_url,
        "slug": item.slug,
        "usuario": item.usuario.username,
        "usuario_id": item.usuario_id,
        "categoria": item.categoria.nome if item.categoria else None,
        "categoria_id": item.categoria_id,
        "criado_em": item.criado_em.isoformat() if item.criado_em else "",
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def api_items(request):
    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "todos").strip().lower()
    categoria_id = request.GET.get("categoria")
    try:
        page = max(1, int(request.GET.get("page", 1)))
        per_page = min(100, max(1, int(request.GET.get("per_page", 20))))
    except (TypeError, ValueError):
        page, per_page = 1, 20

    qs = Item.objects.select_related("usuario", "categoria").order_by("-id")
    if q:
        qs = qs.filter(Q(titulo__icontains=q) | Q(descricao__icontains=q) | Q(local__icontains=q))
    if status in ["perdido", "achado", "devolvido"]:
        qs = qs.filter(status=status)
    if categoria_id and str(categoria_id).isdigit():
        qs = qs.filter(categoria_id=int(categoria_id))

    start = (page - 1) * per_page
    items_page = list(qs[start:start + per_page + 1])
    has_more = len(items_page) > per_page
    items_page = items_page[:per_page]

    return Response({"ok": True, "results": [_item_to_dict(i, request) for i in items_page], "page": page, "has_more": has_more})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_item_detail(request, item_id):
    try:
        item = Item.objects.select_related("usuario", "categoria").get(id=item_id)
    except Item.DoesNotExist:
        return Response({"ok": False, "detail": "Item não encontrado."}, status=404)
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_create_item(request):
    data = request.POST if request.POST else request.data
    titulo = (data.get("titulo") or "").strip()
    descricao = (data.get("descricao") or "").strip()
    local = (data.get("local") or "").strip()
    status = (data.get("status") or "perdido").strip().lower()
    categoria_id = data.get("categoria")
    data_item = data.get("data") or str(datetime.date.today())

    if not titulo:
        return Response({"ok": False, "detail": "Título é obrigatório."}, status=400)
    if status not in ["perdido", "achado", "devolvido"]:
        status = "perdido"

    categoria = None
    if categoria_id:
        try:
            categoria = Categoria.objects.get(id=categoria_id)
        except Categoria.DoesNotExist:
            pass

    imagem = request.FILES.get("imagem")
    item = Item.objects.create(
        titulo=titulo, descricao=descricao, local=local,
        status=status, categoria=categoria, usuario=request.user,
        data=data_item, imagem=imagem,
    )
    return Response({"ok": True, "data": _item_to_dict(item, request)}, status=201)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def api_edit_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    data = request.POST if request.POST else request.data
    if "titulo" in data and data["titulo"]:
        item.titulo = data["titulo"].strip()
    if "descricao" in data:
        item.descricao = data["descricao"].strip()
    if "local" in data:
        item.local = data["local"].strip()
    if "status" in data and data["status"] in ["perdido", "achado", "devolvido"]:
        item.status = data["status"]
    if "categoria" in data:
        try:
            item.categoria = Categoria.objects.get(id=data["categoria"])
        except (Categoria.DoesNotExist, ValueError, TypeError):
            pass
    if "data" in data:
        item.data = data["data"]
    if request.FILES.get("imagem"):
        item.imagem = request.FILES["imagem"]
    item.save()
    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def api_delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, usuario=request.user)
    item.delete()
    return Response({"ok": True, "detail": "Item deletado com sucesso."})


@api_view(["POST", "PATCH"])
@permission_classes([IsAuthenticated])
def api_change_item_status(request, item_id):
    from items.models import AcaoLog
    
    item = get_object_or_404(Item, id=item_id)
    is_admin = request.user.groups.filter(name="Administradores").exists() or request.user.is_staff
    is_bolsista = request.user.groups.filter(name="Bolsistas").exists()
    is_owner = item.usuario == request.user

    if not (is_admin or is_bolsista or is_owner):
        return Response({"ok": False, "detail": "Item não encontrado."}, status=404)

    novo_status = (request.data.get("status") or "").strip().lower()
    valid_statuses = ["perdido", "achado", "devolvido", "confirmado", "pendente_confirmacao"]
    if novo_status not in valid_statuses:
        return Response({"ok": False, "detail": "Status inválido."}, status=400)

    # Lógica para Usuário comum (dono)
    if not is_admin and not is_bolsista:
        if novo_status not in ["achado", "perdido"]:
            return Response({
                "ok": False,
                "detail": "Usuários comuns só podem alterar o status de seus próprios itens para 'achado' ou 'perdido'."
            }, status=403)

    # Lógica para Bolsista
    elif is_bolsista and not is_admin:
        if novo_status not in ["confirmado", "devolvido"]:
            if is_owner and novo_status in ["achado", "perdido"]:
                pass
            else:
                return Response({
                    "ok": False,
                    "detail": "Bolsistas só podem alterar o status para 'confirmado' ou 'devolvido'."
                }, status=403)

    # Administrador pode tudo.

    observacao = request.data.get("observacao", "").strip()
    nome_recebedor = request.data.get("nome_recebedor", "").strip()
    
    if novo_status == "devolvido":
        observacao_log = f"Status alterado para devolvido"
        if nome_recebedor:
            observacao_log += f". Recebedor: {nome_recebedor}"
        if observacao:
            observacao_log += f" | Obs: {observacao}"
    else:
        observacao_log = observacao or f"Status alterado para {novo_status}"

    item.status = novo_status
    item.save(update_fields=["status", "atualizado_em"])

    # Cria AcaoLog se for alterado por bolsista/admin para confirmado ou devolvido
    if (is_bolsista or is_admin) and novo_status in ["confirmado", "devolvido"]:
        acao_tipo = "confirmou" if novo_status == "confirmado" else "devolveu"
        AcaoLog.objects.create(
            bolsista=request.user,
            item=item,
            acao=acao_tipo,
            observacao=observacao_log,
            ip_origem=_get_client_ip(request)
        )

    return Response({"ok": True, "data": _item_to_dict(item, request)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_my_items(request):
    try:
        page = max(1, int(request.GET.get("page", 1)))
        per_page = min(100, max(1, int(request.GET.get("per_page", 20))))
    except (TypeError, ValueError):
        page, per_page = 1, 20
    qs = Item.objects.filter(usuario=request.user).select_related("categoria").order_by("-id")
    start = (page - 1) * per_page
    items_page = list(qs[start:start + per_page + 1])
    has_more = len(items_page) > per_page
    items_page = items_page[:per_page]
    return Response({"ok": True, "results": [_item_to_dict(i, request) for i in items_page], "page": page, "has_more": has_more})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_stats(request):
    from django.db.models.functions import TruncMonth
    from django.db.models import Count, Avg, ExpressionWrapper, F, DurationField
    from datetime import date, timedelta
    from django.utils import timezone

    # 1. Total e status base
    total = Item.objects.count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()
    devolvidos = Item.objects.filter(status="devolvido").count()
    confirmados = Item.objects.filter(status="confirmado").count()

    # 2. Novos cadastros hoje e esta semana
    hoje = timezone.now().date()
    semana = hoje - timedelta(days=7)
    cadastros_hoje = Item.objects.filter(criado_em__date=hoje).count()
    cadastros_semana = Item.objects.filter(criado_em__date__gte=semana).count()

    # 3. Evolução mensal dos últimos 6 meses
    seis_meses = hoje - timedelta(days=180)
    evolucao_qs = (
        Item.objects
        .filter(criado_em__date__gte=seis_meses)
        .annotate(mes=TruncMonth('criado_em'))
        .values('mes', 'status')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    evolucao_mensal = list(evolucao_qs)

    # 4. Itens por categoria (top 6)
    por_categoria = list(
        Item.objects
        .values('categoria__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )

    # 5. Tempo médio de resolução por categoria para itens devolvidos
    tempo_resolucao_qs = (
        Item.objects
        .filter(status='devolvido')
        .annotate(duracao=ExpressionWrapper(
            F('atualizado_em') - F('criado_em'),
            output_field=DurationField()
        ))
        .values('categoria__nome')
        .annotate(media_dias=Avg('duracao'))
        .order_by('categoria__nome')
    )
    tempo_resolucao = list(tempo_resolucao_qs)
    for entry in tempo_resolucao:
        val = entry.get('media_dias')
        if val is not None:
            if hasattr(val, 'total_seconds'):
                entry['media_dias'] = val.total_seconds() * 1000000.0
            else:
                entry['media_dias'] = float(val)
        else:
            entry['media_dias'] = 0.0

    return Response({"ok": True, "data": {
        "total": total,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "confirmados": confirmados,
        "cadastros_hoje": cadastros_hoje,
        "cadastros_semana": cadastros_semana,
        "por_categoria": por_categoria,
        "evolucao_mensal": evolucao_mensal,
        "tempo_resolucao": tempo_resolucao,
    }})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_categories(request):
    cats = Categoria.objects.all().values("id", "nome")
    return Response({"ok": True, "results": list(cats)})


@api_view(["POST"])
@permission_classes([AllowAny])
def api_search_by_image(request):
    """Busca itens visualmente similares a uma foto enviada (AI visual search)."""
    imagem = request.FILES.get("imagem") or request.FILES.get("image")
    if not imagem:
        return Response({"ok": False, "detail": "Envie uma imagem no campo 'imagem'."}, status=400)

    try:
        resultados = Item.buscar_por_imagem(imagem)
        items_data = []
        for item, similaridade in resultados:
            d = _item_to_dict(item, request)
            d["similaridade"] = similaridade
            items_data.append(d)

        return Response({
            "ok": True,
            "total": len(items_data),
            "results": items_data,
        })
    except Exception as e:
        return Response({"ok": False, "detail": f"Erro ao processar imagem: {str(e)}"}, status=500)


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(["GET"])
@permission_classes([AllowAny])
def api_item_qr_image(request, slug):
    from django.http import HttpResponse
    from items.models import ArquivoMidia, Item
    nome_qr = f"qr_{slug}.png"
    try:
        arquivo = ArquivoMidia.objects.get(nome=nome_qr)
        return HttpResponse(arquivo.conteudo, content_type=arquivo.content_type)
    except ArquivoMidia.DoesNotExist:
        try:
            # Se a etiqueta ainda não existe no banco, tenta gerar na hora
            item = Item.objects.get(slug=slug)
            item._gerar_qrcode()
            arquivo = ArquivoMidia.objects.get(nome=nome_qr)
            return HttpResponse(arquivo.conteudo, content_type=arquivo.content_type)
        except Exception:
            return Response({"ok": False, "detail": "Imagem de QR Code não encontrada para este item."}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBolsistaOuAdmin])
def api_item_qr_scan(request, slug):
    from accounts.permissoes import IsBolsistaOuAdmin
    from items.models import AcaoLog
    
    item = get_object_or_404(Item, slug=slug)
    observacao = request.data.get("observacao", "").strip() or "Item físico conferido no balcão"

    item.status = "confirmado"
    item.save(update_fields=["status", "atualizado_em"])

    AcaoLog.objects.create(
        bolsista=request.user,
        item=item,
        acao="confirmou",
        observacao=observacao,
        ip_origem=_get_client_ip(request)
    )

    return Response({
        "ok": True,
        "detail": f"Item '{item.titulo}' confirmado com sucesso no balcão.",
        "item": _item_to_dict(item, request)
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsBolsistaOuAdmin])
def api_bolsista_pendentes(request):
    from accounts.permissoes import IsBolsistaOuAdmin
    try:
        page = max(1, int(request.GET.get("page", 1)))
        per_page = min(100, max(1, int(request.GET.get("per_page", 20))))
    except (TypeError, ValueError):
        page, per_page = 1, 20

    qs = Item.objects.filter(status__in=["achado", "pendente_confirmacao"]).select_related("usuario", "categoria").order_by("-id")
    
    start = (page - 1) * per_page
    items_page = list(qs[start:start + per_page + 1])
    has_more = len(items_page) > per_page
    items_page = items_page[:per_page]

    return Response({
        "ok": True,
        "results": [_item_to_dict(i, request) for i in items_page],
        "page": page,
        "has_more": has_more
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBolsistaOuAdmin])
def api_bolsista_confirmar(request, item_id):
    from accounts.permissoes import IsBolsistaOuAdmin
    from items.models import AcaoLog
    
    item = get_object_or_404(Item, id=item_id)
    observacao = request.data.get("observacao", "").strip() or "Confirmado fisicamente no balcão"

    item.status = "confirmado"
    item.save(update_fields=["status", "atualizado_em"])

    AcaoLog.objects.create(
        bolsista=request.user,
        item=item,
        acao="confirmou",
        observacao=observacao,
        ip_origem=_get_client_ip(request)
    )

    return Response({
        "ok": True,
        "detail": f"Item '{item.titulo}' confirmado com sucesso.",
        "item": _item_to_dict(item, request)
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsBolsistaOuAdmin])
def api_bolsista_devolver(request, item_id):
    from accounts.permissoes import IsBolsistaOuAdmin
    from items.models import AcaoLog
    
    item = get_object_or_404(Item, id=item_id)
    nome_recebedor = request.data.get("nome_recebedor", "").strip()
    if not nome_recebedor:
        return Response({"ok": False, "detail": "O campo 'nome_recebedor' é obrigatório."}, status=400)

    obs_extra = request.data.get("observacao", "").strip()
    observacao_log = f"Recebedor: {nome_recebedor}"
    if obs_extra:
        observacao_log += f" | Obs: {obs_extra}"

    item.status = "devolvido"
    item.save(update_fields=["status", "atualizado_em"])

    AcaoLog.objects.create(
        bolsista=request.user,
        item=item,
        acao="devolveu",
        observacao=observacao_log,
        ip_origem=_get_client_ip(request)
    )

    return Response({
        "ok": True,
        "detail": f"Devolução do item '{item.titulo}' registrada com sucesso para {nome_recebedor}.",
        "item": _item_to_dict(item, request)
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsBolsistaOuAdmin])
def api_bolsista_meu_log(request):
    from accounts.permissoes import IsBolsistaOuAdmin
    from items.models import AcaoLog
    
    logs = AcaoLog.objects.filter(bolsista=request.user).select_related("item").order_by("-timestamp")[:50]
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "item_id": log.item_id,
            "item_titulo": log.item.titulo if log.item else "Item removido",
            "acao": log.acao,
            "acao_display": log.get_acao_display(),
            "timestamp": log.timestamp.isoformat(),
            "observacao": log.observacao,
            "ip_origem": log.ip_origem
        })
    return Response({"ok": True, "results": results})
