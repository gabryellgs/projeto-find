from datetime import date

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ProfileupdateForm
from .models import Categoria, Item, Profile, Chat, Mensagem


# -----------------------------
# Helpers
# -----------------------------
def _get_stripped(request, key, default=""):
    return (request.GET.get(key) or default).strip()


def _get_int(request, key, default=1):
    try:
        return int(request.GET.get(key, default))
    except (TypeError, ValueError):
        return default


def _apply_item_filters(itens_qs, q="", status="todos", categoria="todas"):
    if q:
        itens_qs = itens_qs.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    # suporta perdido, achado e devolvido
    if status in ["perdido", "achado", "devolvido"]:
        itens_qs = itens_qs.filter(status=status)

    if categoria.isdigit():
        itens_qs = itens_qs.filter(categoria_id=int(categoria))

    return itens_qs


def _paginate_has_more(qs, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    itens_list = list(qs[start:end + 1])
    has_more = len(itens_list) > per_page
    return itens_list[:per_page], has_more


def _system_counts():
    total = Item.objects.count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()
    devolvidos = Item.objects.filter(status="devolvido").count()
    return total, perdidos, encontrados, devolvidos


def _usuario_participa(chat, user):
    return user.id in (chat.criado_por_id, chat.dono_item_id)


# -----------------------------
# Home / Auth
# -----------------------------
def home(request):
    total, perdidos, encontrados, devolvidos = _system_counts()

    return render(request, "mainpage/index.html", {
        "total_itens": total,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
    })

def login_view(request):
    if request.method == "POST":
        email_or_username = request.POST.get("username")
        password = request.POST.get("password")

        # tenta achar usuário pelo email
        user_obj = User.objects.filter(email=email_or_username).first()
        if user_obj:
            username = user_obj.username
        else:
            username = email_or_username

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Bem-vindo, {user.username}!")
            return redirect("menu")

        messages.error(request, "Usuário, e-mail ou senha incorretos.")

    return render(request, "mainpage/login.html")


def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        data_nascimento = request.POST.get("data_nascimento")
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # valida data + idade mínima
        dn_value = None
        if data_nascimento:
            try:
                dn_value = date.fromisoformat(data_nascimento)
            except ValueError:
                messages.error(request, "Data de nascimento inválida.")
                return redirect("register")

            hoje = date.today()
            if dn_value > hoje:
                messages.error(request, "Data de nascimento inválida.")
                return redirect("register")

            idade = hoje.year - dn_value.year - (
                (hoje.month, hoje.day) < (dn_value.month, dn_value.day)
            )
            if idade < 13:
                messages.error(request, "Você precisa ter pelo menos 13 anos para criar uma conta.")
                return redirect("register")

        if password != confirm_password:
            messages.error(request, "As senhas não coincidem.")
            return redirect("register")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Nome de usuário já existe.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Esse e-mail já está em uso.")
            return redirect("register")



        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        profile, _ = Profile.objects.get_or_create(user=user)

        if dn_value:
            profile.data_nascimento = dn_value
            profile.save(update_fields=["data_nascimento"])

        messages.success(request, "Conta criada com sucesso! Faça login.")
        return redirect("login")

    return render(request, "mainpage/register.html")


# -----------------------------
# Menu / Perfil
# -----------------------------
@login_required(login_url="login")
def menu_search_suggestions(request):
    q = _get_stripped(request, "q", "")
    if not q:
        return JsonResponse([], safe=False)

    itens = Item.objects.filter(
        Q(titulo__icontains=q) |
        Q(descricao__icontains=q) |
        Q(local__icontains=q)
    ).select_related('categoria').order_by("-id")[:8]

    suggestions = [
        {
            "titulo": item.titulo,
            "subtitulo": item.local or (item.categoria.nome if item.categoria else ""),
            "url": reverse("item_detail", args=[item.slug])
        }
        for item in itens
    ]
    return JsonResponse(suggestions, safe=False)

@login_required(login_url="login")
def menu_view(request):
    categorias = Categoria.objects.all()

    q = _get_stripped(request, "q", "")
    status = _get_stripped(request, "status", "todos")
    categoria = _get_stripped(request, "categoria", "todas")

    base_qs = Item.objects.select_related('usuario', 'categoria').all().order_by("-id")

    # lista principal (com filtros)
    itens = _apply_item_filters(base_qs, q=q, status=status, categoria=categoria)

    # listas específicas para seções
    itens_devolvidos = Item.objects.filter(status="devolvido").select_related('usuario', 'categoria').order_by("-id")[:10]
    itens_perdidos = Item.objects.filter(status="perdido").select_related('usuario', 'categoria').order_by("-id")[:10]
    itens_achados = Item.objects.filter(status="achado").select_related('usuario', 'categoria').order_by("-id")[:10]

    total_itens, perdidos, encontrados, devolvidos = _system_counts()

    return render(request, "mainpage/menu.html", {
        "categorias": categorias,
        "itens": itens,
        "itens_devolvidos": itens_devolvidos,
        "itens_perdidos": itens_perdidos,
        "itens_achados": itens_achados,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "q": q,
        "status": status,
        "categoria": categoria,
    })

@login_required(login_url="login")
def screen_user(request):
    user = request.user
    itens = Item.objects.filter(usuario=user).select_related('categoria').order_by("-id")
    categorias = Categoria.objects.all()

    return render(request, "mainpage/user.html", {
        "nome": user.get_full_name() or user.username,
        "email": user.email,
        "itens": itens,
        "total": itens.count(),
        "perdidos": itens.filter(status="perdido").count(),
        "encontrados": itens.filter(status="achado").count(),
        "devolvidos": itens.filter(status="devolvido").count(),
        "categorias": categorias,
    })


@login_required(login_url="login")
def upload_photo(request):
    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=request.user)
        form = ProfileupdateForm(request.POST, request.FILES, instance=profile)

        if form.is_valid():
            form.save()
            messages.success(request, "Foto atualizada com sucesso!")
        else:
            messages.error(request, "Erro ao processar a imagem.")

    return redirect("screen_user")


@login_required(login_url="login")
def update_profile(request):
    if request.method == "POST":
        user = request.user
        profile, _ = Profile.objects.get_or_create(user=user)

        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        user.save(update_fields=["first_name", "last_name"])

        profile.telefone = request.POST.get("telefone")
        profile.cidade = request.POST.get("cidade")
        profile.estado = request.POST.get("estado")
        profile.cep = request.POST.get("cep")

        if request.FILES.get("image"):
            profile.image = request.FILES.get("image")

        profile.save()
        messages.success(request, "Perfil atualizado com sucesso!")

    return redirect("screen_user")


# -----------------------------
# Itens CRUD
# -----------------------------
@login_required(login_url="login")
def register_item(request):
    next_url = request.GET.get("next") or reverse("screen_user")

    if request.method != "POST":
        return redirect(next_url)

    titulo = (request.POST.get("titulo") or "").strip()
    descricao = request.POST.get("descricao") or ""
    categoria_id = request.POST.get("categoria")
    status = request.POST.get("status")
    data_item = request.POST.get("data")
    local = request.POST.get("local") or ""
    imagem = request.FILES.get("imagem")

    if not titulo or len(titulo) < 3:
        messages.error(request, "O nome do item é obrigatório e deve ter pelo menos 3 caracteres.")
        return redirect(next_url)

    categoria = Categoria.objects.filter(id=categoria_id).first() if categoria_id else None

    Item.objects.create(
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        status=status,
        usuario=request.user,
        data=data_item,
        local=local,
        imagem=imagem,
    )

    messages.success(request, "Item cadastrado com sucesso!")
    return redirect(next_url)


@login_required(login_url="login")
def edit_item(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    categorias = Categoria.objects.all()
    next_url = request.GET.get("next") or reverse("screen_user")

    if request.method == "POST":
        item.titulo = request.POST.get("titulo", item.titulo)
        item.descricao = request.POST.get("descricao", item.descricao)
        item.local = request.POST.get("local", item.local)
        item.status = request.POST.get("status", item.status)
        item.data = request.POST.get("data", item.data)

        categoria_id = request.POST.get("categoria")
        if categoria_id:
            item.categoria_id = categoria_id

        if request.FILES.get("imagem"):
            item.imagem = request.FILES.get("imagem")

        item.save()
        messages.success(request, "Item atualizado com sucesso!")
        return redirect(next_url)

    return render(request, "mainpage/item_edit.html", {
        "item": item,
        "categorias": categorias,
        "next": next_url,
    })


@login_required(login_url="login")
def delete_item(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    next_url = request.GET.get("next") or reverse("screen_user")

    if request.method == "POST":
        item.delete()
        messages.success(request, "Item deletado com sucesso!")
        return redirect(next_url)

    return render(request, "mainpage/item_confirm_delete.html", {
        "item": item,
        "next": next_url,
    })


# -----------------------------
# Listagens de itens
# -----------------------------
@login_required(login_url="login")
def list_item(request):
    categorias = Categoria.objects.all()

    q = _get_stripped(request, "q", "")
    status = _get_stripped(request, "status", "todos")
    categoria = _get_stripped(request, "categoria", "todas")
    page = _get_int(request, "page", 1)

    itens = Item.objects.all().order_by("-id")
    itens = _apply_item_filters(itens, q=q, status=status, categoria=categoria)

    per_page = 8
    itens_page, has_more = _paginate_has_more(itens, page=page, per_page=per_page)

    total_itens, perdidos, encontrados, devolvidos = _system_counts()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "q": q,
        "status": status,
        "categoria": categoria,
        "page_title": "Todos os itens",
        "has_more": has_more,
        "next_page": page + 1,
    })


@login_required(login_url="login")
def my_itens(request):
    q = _get_stripped(request, "q", "")
    status = _get_stripped(request, "status", "")
    page = _get_int(request, "page", 1)

    itens = Item.objects.filter(usuario=request.user).order_by("-id")

    if q:
        itens = itens.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    if status in ["perdido", "achado", "devolvido"]:
        itens = itens.filter(status=status)

    per_page = 8
    itens_page, has_more = _paginate_has_more(itens, page=page, per_page=per_page)

    return render(request, "mainpage/my_itens.html", {
        "itens": itens_page,
        "q": q,
        "status": status,
        "has_more": has_more,
        "next_page": page + 1,
        "page_title": "Meus itens",
    })


@login_required(login_url="login")
def items_perdidos(request):
    categorias = Categoria.objects.all()

    q = _get_stripped(request, "q", "")
    categoria = _get_stripped(request, "categoria", "todas")
    page = _get_int(request, "page", 1)

    itens = Item.objects.filter(status="perdido").order_by("-id")
    itens = _apply_item_filters(itens, q=q, status="perdido", categoria=categoria)

    per_page = 8
    itens_page, has_more = _paginate_has_more(itens, page=page, per_page=per_page)

    total_itens, perdidos, encontrados, devolvidos = _system_counts()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "q": q,
        "status": "perdido",
        "categoria": categoria,
        "page_title": "Itens Perdidos",
        "has_more": has_more,
        "next_page": page + 1,
    })


@login_required(login_url="login")
def items_encontrados(request):
    categorias = Categoria.objects.all()

    q = _get_stripped(request, "q", "")
    categoria = _get_stripped(request, "categoria", "todas")
    page = _get_int(request, "page", 1)

    itens = Item.objects.filter(status="achado").order_by("-id")
    itens = _apply_item_filters(itens, q=q, status="achado", categoria=categoria)

    per_page = 8
    itens_page, has_more = _paginate_has_more(itens, page=page, per_page=per_page)

    total_itens, perdidos, encontrados, devolvidos = _system_counts()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "q": q,
        "status": "achado",
        "categoria": categoria,
        "page_title": "Itens Encontrados",
        "has_more": has_more,
        "next_page": page + 1,
    })


@login_required(login_url="login")
def items_devolvidos(request):
    categorias = Categoria.objects.all()

    q = _get_stripped(request, "q", "")
    categoria = _get_stripped(request, "categoria", "todas")
    page = _get_int(request, "page", 1)

    itens = Item.objects.filter(status="devolvido").order_by("-id")
    itens = _apply_item_filters(itens, q=q, status="devolvido", categoria=categoria)

    per_page = 8
    itens_page, has_more = _paginate_has_more(itens, page=page, per_page=per_page)

    total_itens, perdidos, encontrados, devolvidos = _system_counts()

    return render(request, "mainpage/item_list.html", {
        "categorias": categorias,
        "itens": itens_page,
        "total_itens": total_itens,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "q": q,
        "status": "devolvido",
        "categoria": categoria,
        "page_title": "Itens Devolvidos",
        "has_more": has_more,
        "next_page": page + 1,
    })


# -----------------------------
# Ação: marcar item como devolvido
# -----------------------------
@login_required(login_url="login")
@require_POST
def marcar_devolvido(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    next_url = request.POST.get("next") or reverse("item_detail", kwargs={"slug": item.slug})

    item.status = "devolvido"
    item.save(update_fields=["status", "atualizado_em"])

    messages.success(request, "Item marcado como devolvido!")
    return redirect(next_url)

# -----------------------------
# Ação: marcar item como achado
# -----------------------------
@login_required(login_url="login")
@require_POST
def marcar_achado(request, id):
    # volta pra página atual (item_detail) se vier next
    item = get_object_or_404(Item, id=id, usuario=request.user)
    next_url = request.POST.get("next") or reverse("item_detail", kwargs={"slug": item.slug})

    item.status = "achado"
    item.save(update_fields=["status", "atualizado_em"])

    messages.success(request, "Item marcado como encontrado!")
    return redirect(next_url)

@login_required(login_url="login")
@require_POST
def marcar_perdido(request, id):
    item = get_object_or_404(Item, id=id, usuario=request.user)
    next_url = request.POST.get("next") or reverse("item_detail", kwargs={"slug": item.slug})
 
    item.status = "perdido"
    item.save(update_fields=["status", "atualizado_em"])
 
    messages.success(request, "Item marcado como perdido!")
    return redirect(next_url)
 
# -----------------------------
# Detalhe do item
# -----------------------------
def item_detail(request, slug):
    item = get_object_or_404(Item, slug=slug)
    next_url = request.GET.get("next") or ""
    return render(request, "mainpage/item_detail.html", {
        "item": item,
        "next": next_url,
    })


@login_required(login_url="login")
def recent_items(request):
    q = _get_stripped(request, "q", "")
    page = _get_int(request, "page", 1)

    itens = Item.objects.all().order_by("-id")

    if q:
        itens = itens.filter(
            Q(titulo__icontains=q) |
            Q(descricao__icontains=q) |
            Q(local__icontains=q)
        )

    per_page = 8
    itens_page, has_more = _paginate_has_more(itens, page=page, per_page=per_page)

    return render(request, "mainpage/item_list.html", {
        "itens": itens_page,
        "q": q,
        "page_title": "Itens Recentes",
        "has_more": has_more,
        "next_page": page + 1,
    })


@login_required(login_url="login")
def view_item(request, id):
    item = get_object_or_404(Item, id=id)
    next_url = request.GET.get("next") or reverse("menu")
    return render(request, "mainpage/item_detail.html", {
        "item": item,
        "next": next_url,
    })


# -----------------------------
# Chats (corrigido + AJAX)
# -----------------------------
@login_required(login_url="login")
def chat_start(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    next_url = request.GET.get("next") or reverse("item_detail", kwargs={"slug": item.slug})

    if item.usuario_id == request.user.id:
        messages.error(request, "Você não pode iniciar um chat com você mesmo.")
        return redirect(next_url)

    chat, _ = Chat.objects.get_or_create(
        item=item,
        criado_por=request.user,
        dono_item=item.usuario,
        defaults={"status": "ativo"},
    )

    if chat.status != "ativo":
        chat.status = "ativo"
        chat.save(update_fields=["status"])

    return redirect("chat_detail", chat_id=chat.id)


@login_required(login_url="login")
def chats_list(request):
    chats = (
        Chat.objects
        .filter(Q(criado_por=request.user) | Q(dono_item=request.user))
        .select_related("item", "criado_por", "dono_item")
        .order_by("-atualizado_em", "-criado_em")
    )
    return render(request, "mainpage/chats_list.html", {"chats": chats})


@login_required(login_url="login")
def chat_detail(request, chat_id):
    chat = get_object_or_404(
        Chat.objects.select_related("item", "criado_por", "dono_item"),
        id=chat_id,
    )

    if not _usuario_participa(chat, request.user):
        messages.error(request, "Você não tem acesso a esse chat.")
        return redirect("chats_list")

    other_user = chat.criado_por if request.user.id == chat.dono_item_id else chat.dono_item
    other_profile = Profile.objects.filter(user=other_user).first()

    mensagens = (
        Mensagem.objects
        .filter(chat=chat)
        .select_related("remetente")
        .order_by("data_envio")
    )

    return render(request, "mainpage/chat_detail.html", {
        "chat": chat,
        "mensagens": mensagens,
        "other_user": other_user,
        "other_profile": other_profile,
    })


@login_required(login_url="login")
def chat_messages(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not _usuario_participa(chat, request.user):
        return JsonResponse({"error": "Você não tem acesso a esse chat."}, status=403)

    Mensagem.objects.filter(chat=chat, lida=False).exclude(remetente=request.user).update(lida=True)

    mensagens = (
        Mensagem.objects
        .filter(chat=chat)
        .select_related("remetente")
        .order_by("data_envio")
    )

    data = [{
        "id": m.id,
        "conteudo": m.conteudo,
        "remetente": m.remetente.username,
        "is_me": (m.remetente_id == request.user.id),
        "data_envio": m.data_envio.strftime("%d/%m/%Y %H:%M"),
    } for m in mensagens]

    return JsonResponse({"chat_id": chat.id, "status": chat.status, "mensagens": data})


@login_required(login_url="login")
@require_POST
def chat_send_message(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not _usuario_participa(chat, request.user):
        return JsonResponse({"error": "Você não tem acesso a esse chat."}, status=403)

    if chat.status != "ativo":
        return JsonResponse({"error": "Esse chat está fechado."}, status=400)

    conteudo = (request.POST.get("conteudo") or "").strip()
    if not conteudo:
        return JsonResponse({"error": "Digite uma mensagem."}, status=400)

    m = Mensagem.objects.create(
        chat=chat,
        remetente=request.user,
        conteudo=conteudo,
        tipo="texto",
        lida=False,
    )

    chat.atualizado_em = timezone.now()
    chat.save(update_fields=["atualizado_em"])

    return JsonResponse({
        "ok": True,
        "mensagem": {
            "id": m.id,
            "conteudo": m.conteudo,
            "remetente": m.remetente.username,
            "is_me": True,
            "data_envio": m.data_envio.strftime("%d/%m/%Y %H:%M"),
        }
    })


@login_required(login_url="login")
@require_POST
def chat_close(request, chat_id):
    chat = get_object_or_404(Chat, id=chat_id)

    if not _usuario_participa(chat, request.user):
        messages.error(request, "Você não tem acesso a esse chat.")
        return redirect("chats_list")

    if request.user.id != chat.dono_item_id:
        messages.error(request, "Apenas o dono do item pode fechar o chat.")
        return redirect("chat_detail", chat_id=chat.id)

    chat.status = "fechado"
    chat.save(update_fields=["status"])

    messages.info(request, "Chat fechado.")
    return redirect("chat_detail", chat_id=chat.id)


@login_required(login_url="login")
def busca_visual(request):
    resultados = []
    imagem_base64 = None
    
    if request.method == "POST" and request.FILES.get("imagem_busca"):
        imagem_file = request.FILES["imagem_busca"]
        try:
            # Executa a busca
            resultados = Item.buscar_por_imagem(imagem_file)
            
            # Converte a imagem enviada para base64 para exibir como preview
            import base64
            imagem_file.seek(0)
            encoded = base64.b64encode(imagem_file.read()).decode("utf-8")
            imagem_base64 = f"data:{imagem_file.content_type};base64,{encoded}"
        except Exception as e:
            messages.error(request, f"Erro ao processar imagem: {str(e)}")

    return render(request, "mainpage/visual_search.html", {
        "resultados": resultados,
        "imagem_preview": imagem_base64,
    })


@login_required(login_url="login")
def bolsista_dashboard(request):
    from accounts.permissoes import bolsista_required
    from items.models import AcaoLog
    from django.core.exceptions import PermissionDenied

    # Decorator-like behavior inline or check permission
    from accounts.permissoes import check_bolsista_ou_admin
    if not check_bolsista_ou_admin(request.user):
        raise PermissionDenied

    if request.method == "POST":
        action = request.POST.get("action")
        item_id = request.POST.get("item_id")
        
        if action == "confirmar" and item_id:
            item = get_object_or_404(Item, id=item_id)
            item.status = "confirmado"
            item.save(update_fields=["status", "atualizado_em"])
            
            from items.api.views import _get_client_ip
            AcaoLog.objects.create(
                bolsista=request.user,
                item=item,
                acao="confirmou",
                observacao="Confirmado via Painel Web do Bolsista.",
                ip_origem=_get_client_ip(request)
            )
            messages.success(request, f"Item '{item.titulo}' confirmado com sucesso!")
            return redirect("bolsista_dashboard")
            
        elif action == "devolver" and item_id:
            nome_recebedor = request.POST.get("nome_recebedor", "").strip()
            observacao = request.POST.get("observacao", "").strip()
            
            if not nome_recebedor:
                messages.error(request, "O nome do recebedor é obrigatório para devoluções.")
            else:
                item = get_object_or_404(Item, id=item_id)
                item.status = "devolvido"
                item.save(update_fields=["status", "atualizado_em"])
                
                obs_log = f"Status alterado para devolvido. Recebedor: {nome_recebedor}"
                if observacao:
                    obs_log += f" | Obs: {observacao}"
                    
                from items.api.views import _get_client_ip
                AcaoLog.objects.create(
                    bolsista=request.user,
                    item=item,
                    acao="devolveu",
                    observacao=obs_log,
                    ip_origem=_get_client_ip(request)
                )
                messages.success(request, f"Item '{item.titulo}' devolvido para {nome_recebedor}!")
                return redirect("bolsista_dashboard")

    pendentes = Item.objects.filter(status__in=["achado", "pendente_confirmacao"]).order_by("-criado_em")
    recent_actions = AcaoLog.objects.filter(bolsista=request.user).select_related("item").order_by("-timestamp")[:50]
    todos_itens = Item.objects.all().order_by("-criado_em")
    
    return render(request, "mainpage/bolsista_dashboard.html", {
        "pendentes": pendentes,
        "recent_actions": recent_actions,
        "todos_itens": todos_itens,
    })


@login_required(login_url="login")
def admin_dashboard(request):
    from accounts.permissoes import check_admin
    from items.models import AcaoLog, Item
    from django.contrib.auth.models import Group, User
    from django.core.exceptions import PermissionDenied

    if not check_admin(request.user):
        raise PermissionDenied

    if request.method == "POST":
        action = request.POST.get("action")
        
        if action == "adicionar_bolsista":
            email = request.POST.get("email", "").strip()
            try:
                user = User.objects.get(email=email)
                grupo, _ = Group.objects.get_or_create(name="Bolsistas")
                user.groups.add(grupo)
                messages.success(request, f"Usuário {user.username} adicionado ao grupo de Bolsistas!")
            except User.DoesNotExist:
                messages.error(request, "Nenhum usuário encontrado com esse e-mail.")
            return redirect("admin_dashboard")
            
        elif action == "remover_bolsista":
            user_id = request.POST.get("user_id")
            user = get_object_or_404(User, id=user_id)
            try:
                grupo = Group.objects.get(name="Bolsistas")
                user.groups.remove(grupo)
                messages.success(request, f"Usuário {user.username} removido dos Bolsistas.")
            except Group.DoesNotExist:
                messages.error(request, "Grupo Bolsistas não existe.")
            return redirect("admin_dashboard")

    try:
        grupo_bolsistas = Group.objects.get(name="Bolsistas")
        bolsistas = grupo_bolsistas.user_set.all().order_by("username")
    except Group.DoesNotExist:
        bolsistas = User.objects.none()

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

    logs = AcaoLog.objects.select_related("bolsista", "item").order_by("-timestamp")[:100]

    return render(request, "mainpage/admin_dashboard.html", {
        "bolsistas": bolsistas,
        "total": total,
        "por_status": por_status,
        "logs": logs,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "status_filter": status_filter,
    })


@login_required(login_url="login")
def dashboard_admin(request):
    from accounts.permissoes import check_admin
    from django.shortcuts import redirect
    from django.urls import reverse
    from django.core.exceptions import PermissionDenied
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    from django.db.models.functions import TruncMonth
    from django.db.models import Count, Avg, ExpressionWrapper, F, DurationField
    from datetime import date, timedelta
    from django.utils import timezone
    from items.models import Item, Categoria

    if not check_admin(request.user):
        return redirect(f"{reverse('login')}?next={request.path}")

    hoje = timezone.now().date()
    semana = hoje - timedelta(days=7)
    seis_meses = hoje - timedelta(days=180)

    # 1. Total e status base
    total = Item.objects.count()
    perdidos = Item.objects.filter(status="perdido").count()
    encontrados = Item.objects.filter(status="achado").count()
    devolvidos = Item.objects.filter(status="devolvido").count()
    confirmados = Item.objects.filter(status="confirmado").count()
    cadastros_hoje = Item.objects.filter(criado_em__date=hoje).count()
    cadastros_semana = Item.objects.filter(criado_em__date__gte=semana).count()

    stats_dict = {
        "total": total,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "confirmados": confirmados,
        "cadastros_hoje": cadastros_hoje,
        "cadastros_semana": cadastros_semana,
    }

    # 2. Evolução mensal
    evolucao_qs = (
        Item.objects
        .filter(criado_em__date__gte=seis_meses)
        .annotate(mes=TruncMonth('criado_em'))
        .values('mes', 'status')
        .annotate(total=Count('id'))
        .order_by('mes')
    )
    evolucao_list = []
    for e in evolucao_qs:
        evolucao_list.append({
            "mes": e['mes'],
            "status": e['status'],
            "total": e['total']
        })

    # 3. Por Categoria (top 6)
    por_categoria_qs = (
        Item.objects
        .values('categoria__nome')
        .annotate(total=Count('id'))
        .order_by('-total')[:6]
    )
    por_categoria = []
    for c in por_categoria_qs:
        por_categoria.append({
            "categoria__nome": c['categoria__nome'] or "Sem categoria",
            "total": c['total']
        })

    # 4. Tempo médio de resolução
    tempo_qs = (
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
    tempo_list = []
    for t in tempo_qs:
        val = t['media_dias']
        microseconds = 0.0
        if val is not None:
            if hasattr(val, 'total_seconds'):
                microseconds = val.total_seconds() * 1000000.0
              
            else:
                microseconds = float(val)
        tempo_list.append({
            "categoria__nome": t['categoria__nome'] or "Sem categoria",
            "media_dias": microseconds
        })

    context = {
        'stats': stats_dict,
        'evolucao_json': json.dumps(evolucao_list, cls=DjangoJSONEncoder),
        'categorias_json': json.dumps(por_categoria, cls=DjangoJSONEncoder),
        'tempo_json': json.dumps(tempo_list, cls=DjangoJSONEncoder),
    }
    return render(request, 'mainpage/dashboard_admin.html', context)