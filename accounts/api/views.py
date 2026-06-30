"""API views para autenticação e perfil de usuário."""
import json
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Profile
from accounts.permissoes import IsAdministrador


@api_view(["POST"])
@permission_classes([AllowAny])
def api_register(request):
    """Registra um novo usuário e retorna tokens JWT."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        payload = request.POST.dict()

    username = (payload.get("username") or "").strip()
    email = (payload.get("email") or "").strip()
    password = payload.get("password") or ""
    full_name = (payload.get("full_name") or "").strip()
    data_nascimento = payload.get("data_nascimento") or None

    if not username:
        return Response({"ok": False, "detail": "Username é obrigatório."}, status=400)
    if len(password) < 8:
        return Response({"ok": False, "detail": "A senha deve ter pelo menos 8 caracteres."}, status=400)
    if User.objects.filter(username=username).exists():
        return Response({"ok": False, "detail": "Username já está em uso."}, status=400)
    if email and User.objects.filter(email=email).exists():
        return Response({"ok": False, "detail": "E-mail já está em uso."}, status=400)

    parts = full_name.split(" ", 1)
    user = User.objects.create_user(
        username=username, email=email, password=password,
        first_name=parts[0] if parts else "",
        last_name=parts[1] if len(parts) > 1 else "",
        is_active=True,
    )
    profile, _ = Profile.objects.get_or_create(user=user)

    if data_nascimento:
        try:
            from datetime import date as _date
            profile.data_nascimento = _date.fromisoformat(data_nascimento)
            profile.save(update_fields=["data_nascimento"])
        except (ValueError, TypeError):
            pass

    refresh = RefreshToken.for_user(user)
    return Response({
        "ok": True,
        "data": {"user": {"username": user.username, "email": user.email}},
        "tokens": {"access": str(refresh.access_token), "refresh": str(refresh)},
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_profile(request):
    """Retorna o perfil do usuário autenticado."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    foto_url = None
    if profile.image:
        try:
            foto_url = request.build_absolute_uri(profile.image.url)
        except Exception:
            pass
    return Response({
        "ok": True,
        "data": {
            "username": user.username,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "telefone": getattr(profile, 'telefone', '') or '',
            "cidade": getattr(profile, 'cidade', '') or '',
            "estado": getattr(profile, 'estado', '') or '',
            "data_nascimento": str(profile.data_nascimento) if profile.data_nascimento else '',
            "foto": foto_url,
        }
    })


@api_view(["POST", "PUT", "PATCH"])
@permission_classes([IsAuthenticated])
def api_update_profile(request):
    """Atualiza o perfil do usuário autenticado com suporte a tamanho de foto."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    data = request.data

    first_name = data.get("first_name")
    last_name = data.get("last_name")
    full_name = data.get("full_name")

    if full_name:
        parts = full_name.strip().split(" ", 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ""
    else:
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name

    username = data.get("username")
    if username and username != user.username:
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return Response({"ok": False, "detail": "Username já está em uso."}, status=400)
        user.username = username
    user.save()

    if "telefone" in data:
        profile.telefone = data["telefone"]
    if "cidade" in data:
        profile.cidade = data["cidade"]
    if "estado" in data:
        profile.estado = data["estado"]
    if "cep" in data:
        profile.cep = data["cep"]
    if "data_nascimento" in data:
        raw = (data["data_nascimento"] or "").strip()
        if raw:
            try:
                from datetime import date as _date
                profile.data_nascimento = _date.fromisoformat(raw)
            except (ValueError, TypeError):
                return Response(
                    {"ok": False, "detail": "Formato de data inválido. Use AAAA-MM-DD."},
                    status=400,
                )
        else:
            profile.data_nascimento = None

    nova_foto = request.FILES.get("image")
    if nova_foto:
        profile.image = nova_foto

    # Salva sem acionar o processamento automático (usamos update_fields para evitar
    # que o override de save() redimensione com o tamanho padrão antes de saber o tamanho escolhido)
    profile.save(update_fields=[
        'telefone', 'cidade', 'estado', 'cep', 'data_nascimento', 'image'
    ])

    # Aplica o redimensionamento com o tamanho escolhido pelo usuário
    tamanho = (data.get("tamanho") or "medio").strip().lower()
    if tamanho not in Profile.TAMANHOS_VALIDOS:
        tamanho = "medio"
    profile.redimensionar(tamanho)

    # Recarrega do banco para garantir que a URL aponta para o arquivo correto
    profile.refresh_from_db()

    foto_url = None
    if profile.image:
        try:
            foto_url = request.build_absolute_uri(profile.image.url)
        except Exception:
            pass

    return Response({
        "ok": True,
        "detail": "Perfil atualizado com sucesso.",
        "data": {
            "username": user.username,
            "email": user.email,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "telefone": getattr(profile, 'telefone', '') or '',
            "cidade": getattr(profile, 'cidade', '') or '',
            "estado": getattr(profile, 'estado', '') or '',
            "data_nascimento": str(profile.data_nascimento) if profile.data_nascimento else '',
            "foto": foto_url,
            "tamanho_aplicado": tamanho,
            "tamanhos_disponiveis": list(Profile.TAMANHOS_VALIDOS.keys()),
        }
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_resize_photo(request):
    """Redimensiona a foto de perfil existente."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if not profile.image or profile.image.name == 'profile_pics/user.png':
        return Response({"ok": False, "detail": "Nenhuma foto de perfil para redimensionar."}, status=400)

    tamanho = (request.data.get("tamanho") or "medio").strip().lower()
    if tamanho not in Profile.TAMANHOS_VALIDOS:
        return Response({"ok": False, "detail": f"Tamanho inválido. Use: {', '.join(Profile.TAMANHOS_VALIDOS.keys())}"}, status=400)

    profile.redimensionar(tamanho)
    foto_url = None
    try:
        foto_url = request.build_absolute_uri(profile.image.url)
    except Exception:
        pass

    return Response({"ok": True, "detail": f"Foto redimensionada para '{tamanho}'.", "data": {"foto": foto_url, "tamanho_aplicado": tamanho}})


@api_view(["GET"])
@permission_classes([AllowAny])
def api_photo_sizes(request):
    """Retorna os tamanhos de foto de perfil disponíveis."""
    return Response({
        "ok": True,
        "data": {nome: {"label": nome.capitalize(), "pixels": px} for nome, px in Profile.TAMANHOS_VALIDOS.items()}
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdministrador])
def api_admin_bolsistas(request):
    from django.contrib.auth.models import Group
    from accounts.permissoes import IsAdministrador

    try:
        grupo_bolsistas = Group.objects.get(name="Bolsistas")
        users = grupo_bolsistas.user_set.all().order_by("username")
    except Group.DoesNotExist:
        users = User.objects.none()

    results = []
    for u in users:
        results.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "full_name": f"{u.first_name} {u.last_name}".strip()
        })
    return Response({"ok": True, "results": results})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdministrador])
def api_admin_bolsistas_adicionar(request):
    from django.contrib.auth.models import Group
    from accounts.permissoes import IsAdministrador

    email = (request.data.get("email") or "").strip()
    if not email:
        return Response({"ok": False, "detail": "O campo 'email' é obrigatório."}, status=400)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"ok": False, "detail": "Usuário não encontrado com este e-mail."}, status=404)

    grupo_bolsistas, _ = Group.objects.get_or_create(name="Bolsistas")
    if user.groups.filter(name="Bolsistas").exists():
        return Response({"ok": True, "detail": "Usuário já é bolsista."})

    user.groups.add(grupo_bolsistas)
    return Response({"ok": True, "detail": f"Usuário {user.username} adicionado ao grupo de Bolsistas com sucesso."})


@api_view(["DELETE"])
@permission_classes([IsAuthenticated, IsAdministrador])
def api_admin_bolsistas_remover(request, user_id):
    from django.contrib.auth.models import Group
    from accounts.permissoes import IsAdministrador

    user = get_object_or_404(User, id=user_id)
    try:
        grupo_bolsistas = Group.objects.get(name="Bolsistas")
        if not user.groups.filter(name="Bolsistas").exists():
            return Response({"ok": False, "detail": "Usuário não faz parte do grupo de Bolsistas."}, status=400)
        user.groups.remove(grupo_bolsistas)
        return Response({"ok": True, "detail": f"Usuário {user.username} removido do grupo de Bolsistas."})
    except Group.DoesNotExist:
        return Response({"ok": False, "detail": "Grupo Bolsistas não existe."}, status=400)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdministrador])
def api_admin_relatorio(request):
    import datetime
    from items.models import Item
    from accounts.permissoes import IsAdministrador

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")
    status_filter = request.GET.get("status")

    qs = Item.objects.all()

    if data_inicio:
        qs = qs.filter(data__gte=data_inicio)
    if data_fim:
        qs = qs.filter(data__lte=data_fim)
    if status_filter:
        qs = qs.filter(status=status_filter)

    total = qs.count()
    por_status = {
        "achado": qs.filter(status="achado").count(),
        "perdido": qs.filter(status="perdido").count(),
        "confirmado": qs.filter(status="confirmado").count(),
        "devolvido": qs.filter(status="devolvido").count(),
        "pendente_confirmacao": qs.filter(status="pendente_confirmacao").count(),
    }

    periodo_inicio = data_inicio or (str(Item.objects.order_by("data").first().data) if Item.objects.exists() else "")
    periodo_fim = data_fim or str(datetime.date.today())

    return Response({
        "ok": True,
        "data": {
            "total": total,
            "por_status": por_status,
            "periodo": {"inicio": periodo_inicio, "fim": periodo_fim}
        }
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdministrador])
def api_admin_log(request):
    from items.models import AcaoLog
    from accounts.permissoes import IsAdministrador

    bolsista_id = request.GET.get("bolsista_id")
    acao_filter = request.GET.get("acao")

    qs = AcaoLog.objects.select_related("bolsista", "item").order_by("-timestamp")

    if bolsista_id:
        qs = qs.filter(bolsista_id=bolsista_id)
    if acao_filter:
        qs = qs.filter(acao=acao_filter)

    logs = qs[:100]
    results = []
    for log in logs:
        results.append({
            "id": log.id,
            "bolsista": {
                "id": log.bolsista.id,
                "username": log.bolsista.username,
                "email": log.bolsista.email
            } if log.bolsista else None,
            "item": {
                "id": log.item.id,
                "titulo": log.item.titulo,
                "slug": log.item.slug
            } if log.item else None,
            "acao": log.acao,
            "acao_display": log.get_acao_display(),
            "timestamp": log.timestamp.isoformat(),
            "observacao": log.observacao,
            "ip_origem": log.ip_origem
        })

    return Response({"ok": True, "results": results})


# ─── Notificações ─────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_notificacoes(request):
    """Lista todas as notificações do usuário autenticado."""
    from items.models import Notificacao
    qs = Notificacao.objects.filter(usuario=request.user).order_by("-criado_em")[:50]
    results = []
    for n in qs:
        results.append({
            "id": n.id,
            "titulo": n.titulo,
            "mensagem": n.mensagem,
            "lida": n.lida,
            "link": n.link or "",
            "icone": n.icone,
            "criado_em": n.criado_em.isoformat(),
        })
    nao_lidas = Notificacao.objects.filter(usuario=request.user, lida=False).count()
    return Response({"ok": True, "results": results, "nao_lidas": nao_lidas})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_notificacao_lida(request, notif_id):
    """Marca uma notificação específica como lida."""
    from items.models import Notificacao
    try:
        notif = Notificacao.objects.get(id=notif_id, usuario=request.user)
        notif.lida = True
        notif.save(update_fields=["lida"])
        return Response({"ok": True, "detail": "Notificação marcada como lida."})
    except Notificacao.DoesNotExist:
        return Response({"ok": False, "detail": "Notificação não encontrada."}, status=404)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def api_notificacoes_marcar_todas_lidas(request):
    """Marca todas as notificações do usuário como lidas."""
    from items.models import Notificacao
    Notificacao.objects.filter(usuario=request.user, lida=False).update(lida=True)
    return Response({"ok": True, "detail": "Todas as notificações foram marcadas como lidas."})

