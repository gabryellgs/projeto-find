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
    if status in ["perdido", "devolvido"]:
        itens_qs = itens_qs.filter(status=status)
    elif status == "achado":
        itens_qs = itens_qs.filter(status__in=["achado", "confirmado"])

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
    encontrados = Item.objects.filter(status__in=["achado", "confirmado"]).count()
    devolvidos = Item.objects.filter(status="devolvido").count()
    return total, perdidos, encontrados, devolvidos


def _usuario_participa(chat, user):
    return user.id in (chat.criado_por_id, chat.dono_item_id)


# -----------------------------
# Home / Auth
# -----------------------------
def home(request):
    total, perdidos, encontrados, devolvidos = _system_counts()
    total_usuarios = User.objects.count()
    ultimos_itens = Item.objects.select_related('categoria').order_by('-criado_em')[:3]
    
    taxa_recuperacao = 0
    if encontrados > 0:
        taxa_recuperacao = int((devolvidos / encontrados) * 100)
    elif devolvidos > 0 and total > 0:
        taxa_recuperacao = int((devolvidos / total) * 100)
        
    # Se a taxa for 0 (sistema novo), coloca um valor padrão otimista ou 0.
    if taxa_recuperacao == 0 and total > 0:
        taxa_recuperacao = 100 if devolvidos == encontrados and devolvidos > 0 else 0

    return render(request, "mainpage/index.html", {
        "total_itens": total,
        "perdidos": perdidos,
        "encontrados": encontrados,
        "devolvidos": devolvidos,
        "total_usuarios": total_usuarios,
        "ultimos_itens": ultimos_itens,
        "taxa_recuperacao": taxa_recuperacao,
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
    itens_achados = Item.objects.filter(status__in=["achado", "confirmado"]).select_related('usuario', 'categoria').order_by("-id")[:10]


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
        "encontrados": itens.filter(status__in=["achado", "confirmado"]).count(),
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
    categorias = Categoria.objects.all()

    if request.method != "POST":
        # Permite pré-preencher o RFID vindo do painel IoT (Tags Pendentes)
        rfid_prefill = request.GET.get("rfid_uid", "").strip().upper()
        return render(request, "mainpage/register_item.html", {
            "categorias": categorias,
            "next": next_url,
            "rfid_prefill": rfid_prefill,
        })

    titulo = (request.POST.get("titulo") or "").strip()
    descricao = request.POST.get("descricao") or ""
    categoria_id = request.POST.get("categoria")
    status = request.POST.get("status")
    data_item = request.POST.get("data")
    local = request.POST.get("local") or ""
    imagem = request.FILES.get("imagem")
    rfid_uid = (request.POST.get("rfid_uid") or "").strip().upper() or None

    latitude = request.POST.get("latitude")
    longitude = request.POST.get("longitude")

    if not titulo or len(titulo) < 3:
        messages.error(request, "O nome do item é obrigatório e deve ter pelo menos 3 caracteres.")
        return redirect(next_url)

    # Valida se o UID RFID já está em uso por outro item
    if rfid_uid and Item.objects.filter(rfid_uid__iexact=rfid_uid).exists():
        messages.error(request, f"A etiqueta RFID '{rfid_uid}' já está associada a outro item.")
        return redirect(next_url)

    categoria = Categoria.objects.filter(id=categoria_id).first() if categoria_id else None

    # Usuários comuns:
    # Se o item foi "achado" por eles, vai para pendente_confirmacao na COPAC.
    # Se for "perdido", pula a COPAC e vai direto pro mural de perdidos.
    from accounts.permissoes import check_bolsista_ou_admin
    if not check_bolsista_ou_admin(request.user):
        if status == "achado":
            status = "pendente_confirmacao"
        else:
            status = "perdido"

    try:
        lat = float(latitude) if latitude else None
        lng = float(longitude) if longitude else None
    except ValueError:
        lat = lng = None

    Item.objects.create(
        titulo=titulo,
        descricao=descricao,
        categoria=categoria,
        status=status,
        usuario=request.user,
        data=data_item,
        local=local,
        imagem=imagem,
        rfid_uid=rfid_uid,
        latitude=lat,
        longitude=lng,
    )

    if status == "pendente_confirmacao":
        messages.success(request, "Item cadastrado! Ele ficará pendente até a validação pela equipe da COPAC.")
    else:
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
    item.rfid_uid = None  # Libera a tag para ser reutilizada em outro item
    item.save(update_fields=["status", "rfid_uid", "atualizado_em"])

    messages.success(request, "Item marcado como devolvido! A etiqueta RFID foi liberada.")
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

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"chat_id": chat.id})

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

    # Notifica o WebSocket
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{chat.id}",
        {
            "type": "chat_message",
            "id": m.id,
            "message": m.conteudo,
            "remetente": m.remetente.username,
            "remetente_id": m.remetente.id,
            "data_envio": m.data_envio.strftime("%d/%m/%Y %H:%M"),
        }
    )

    # Notifica a outra parte
    destinatario = chat.criado_por if request.user == chat.dono_item else chat.dono_item
    try:
        from items.models import Notificacao
        from django.urls import reverse
        link_chat = reverse('chat_detail', args=[chat.id])
        Notificacao.objects.create(
            usuario=destinatario,
            titulo=f"Nova mensagem de {request.user.first_name or request.user.username}",
            mensagem=f"Sobre o item: {chat.item.titulo}",
            icone="bi-chat-dots-fill",
            link=link_chat
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao criar notificação de chat: {e}")

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


import re
from math import floor

def _calcular_match_score(perdido, achado):
    score = 0
    # Categoria (peso 35)
    if perdido.categoria_id and achado.categoria_id and perdido.categoria_id == achado.categoria_id:
        score += 35
    
    # Palavras-chave Titulo (peso 40)
    p_words = set(re.findall(r'\w+', perdido.titulo.lower() if perdido.titulo else ''))
    a_words = set(re.findall(r'\w+', achado.titulo.lower() if achado.titulo else ''))
    
    stopwords = {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'uma', 'na', 'no'}
    p_words = p_words - stopwords
    a_words = a_words - stopwords
    
    if p_words and a_words:
        overlap = len(p_words.intersection(a_words))
        score += min(40, (overlap / len(p_words)) * 40)
        
    # Palavras-chave Descrição (peso 25)
    p_desc = set(re.findall(r'\w+', perdido.descricao.lower() if perdido.descricao else '')) - stopwords
    a_desc = set(re.findall(r'\w+', achado.descricao.lower() if achado.descricao else '')) - stopwords
    
    if p_desc and a_desc:
        overlap_desc = len(p_desc.intersection(a_desc))
        score += min(25, (overlap_desc / len(p_desc)) * 25)
        
    return floor(score)

@login_required(login_url="login")
def busca_visual(request):
    resultados = []
    imagem_base64 = None
    
    # 1. Busca por imagem (opcional, como já existia)
    if request.method == "POST" and request.FILES.get("imagem_busca"):
        imagem_file = request.FILES["imagem_busca"]
        try:
            resultados = Item.buscar_por_imagem(imagem_file)
            import base64
            imagem_file.seek(0)
            encoded = base64.b64encode(imagem_file.read()).decode("utf-8")
            imagem_base64 = f"data:{imagem_file.content_type};base64,{encoded}"
        except Exception as e:
            messages.error(request, f"Erro ao processar imagem: {str(e)}")

    # 2. Match Automático (Smart Match) para os itens perdidos do usuário
    matches_automaticos = []
    meus_perdidos = Item.objects.filter(usuario=request.user, status="perdido")
    # Busca itens que foram achados ou estão sob custódia
    todos_achados = Item.objects.filter(status__in=["achado", "pendente_confirmacao", "confirmado"]).exclude(usuario=request.user)
    
    for perdido in meus_perdidos:
        lista_matches = []
        for achado in todos_achados:
            score = _calcular_match_score(perdido, achado)
            if score >= 30:  # Filtra apenas quem tem no mínimo 30% de similaridade
                lista_matches.append({
                    "item": achado,
                    "score": score
                })
        
        # Ordena os matches pelo maior score primeiro
        lista_matches.sort(key=lambda x: x['score'], reverse=True)
        
        matches_automaticos.append({
            "perdido": perdido,
            "sugestoes": lista_matches[:6] # Pega até os 6 melhores matches
        })

    return render(request, "mainpage/visual_search.html", {
        "resultados": resultados,
        "imagem_preview": imagem_base64,
        "matches_automaticos": matches_automaticos,
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
            rfid_uid = request.POST.get("rfid_uid", "").strip()
            if rfid_uid:
                item.rfid_uid = rfid_uid
                item.save(update_fields=["status", "rfid_uid", "atualizado_em"])
            else:
                item.save(update_fields=["status", "atualizado_em"])
            
            from items.api.views import _get_client_ip
            obs_log = f"Confirmado via Painel Web do Bolsista."
            if rfid_uid:
                obs_log += f" Tag RFID vinculada: {rfid_uid}"
            AcaoLog.objects.create(
                bolsista=request.user,
                item=item,
                acao="confirmou",
                observacao=obs_log,
                ip_origem=_get_client_ip(request)
            )

            # Notifica o usuário de que o item foi validado na COPAC
            from items.models import Notificacao
            from django.urls import reverse
            try:
                Notificacao.objects.create(
                    usuario=item.usuario,
                    titulo="Item Validado na COPAC! 🎉",
                    mensagem=f"Seu item '{item.titulo}' foi verificado por nossa equipe e está sob custódia física da COPAC. Ele agora aparece no painel de achados.",
                    icone="bi-check-circle-fill",
                    link=reverse('item_detail', args=[item.slug]) if item.slug else "#"
                )
            except Exception:
                pass

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
                item.rfid_uid = None  # Libera a tag RFID para ser reutilizada em outro item
                item.save(update_fields=["status", "rfid_uid", "atualizado_em"])

                # Notifica o dono que o item foi retirado
                from items.models import Notificacao
                try:
                    Notificacao.objects.create(
                        usuario=item.usuario,
                        titulo="Item Entregue/Retirado ✅",
                        mensagem=f"Seu item '{item.titulo}' foi retirado no balcão da COPAC por: {nome_recebedor}.",
                        icone="bi-box-seam",
                    )
                except Exception:
                    pass
                
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
                messages.success(request, f"Item '{item.titulo}' devolvido para {nome_recebedor}! Etiqueta RFID liberada.")
                return redirect("bolsista_dashboard")

        elif action == "editar" and item_id:
            item = get_object_or_404(Item, id=item_id)
            novo_titulo    = (request.POST.get("novo_titulo") or "").strip()
            nova_descricao = (request.POST.get("nova_descricao") or "").strip()
            novo_local     = (request.POST.get("novo_local") or "").strip()
            nova_categoria_id = request.POST.get("nova_categoria")
            novo_rfid      = (request.POST.get("novo_rfid") or "").strip().upper() or None
            nova_imagem    = request.FILES.get("nova_imagem")

            if novo_titulo and len(novo_titulo) >= 3:
                item.titulo = novo_titulo
            if nova_descricao:
                item.descricao = nova_descricao
            if novo_local:
                item.local = novo_local
            if nova_categoria_id:
                nova_cat = Categoria.objects.filter(id=nova_categoria_id).first()
                if nova_cat:
                    item.categoria = nova_cat
            if novo_rfid:
                # Verifica duplicata de RFID em outro item
                if Item.objects.filter(rfid_uid__iexact=novo_rfid).exclude(id=item.id).exists():
                    messages.error(request, f"A etiqueta RFID '{novo_rfid}' já está em uso em outro item.")
                    return redirect("bolsista_dashboard")
                item.rfid_uid = novo_rfid
            if nova_imagem:
                item.imagem = nova_imagem

            item.save()
            messages.success(request, f"Item '{item.titulo}' atualizado com sucesso!")
            return redirect("bolsista_dashboard")

        elif action == "rejeitar" and item_id:
            item = get_object_or_404(Item, id=item_id)
            motivo = (request.POST.get("motivo_rejeicao") or "").strip()
            item.status = "perdido"  # Volta como perdido (visível para o usuário)
            item.save(update_fields=["status", "atualizado_em"])
            messages.warning(request, f"Item '{item.titulo}' rejeitado e marcado como perdido.")
            return redirect("bolsista_dashboard")


    categorias = Categoria.objects.all().order_by("nome")
    pendentes = Item.objects.filter(status__in=["achado", "confirmado", "pendente_confirmacao"]).order_by("-criado_em")
    recent_actions = AcaoLog.objects.filter(bolsista=request.user).select_related("item").order_by("-timestamp")[:50]
    total_acoes = AcaoLog.objects.filter(bolsista=request.user).count()
    devolucoes_count = AcaoLog.objects.filter(bolsista=request.user, acao="devolveu").count()
    todos_itens = Item.objects.all().order_by("-criado_em")

    return render(request, "mainpage/bolsista_dashboard.html", {
        "pendentes": pendentes,
        "recent_actions": recent_actions,
        "total_acoes": total_acoes,
        "devolucoes_count": devolucoes_count,
        "todos_itens": todos_itens,
        "categorias": categorias,
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


# -----------------------------
# IoT — Central de Dispositivos
# -----------------------------
@login_required(login_url="login")
def iot_dashboard(request):
    from iot.models import Dispositivo, LeituraLog

    dispositivos = Dispositivo.objects.all().order_by("-criado_em")

    # Anota leituras de sucesso por dispositivo
    for d in dispositivos:
        d.leituras_sucesso = d.leituras.filter(sucesso_identificacao=True).count()

    total_dispositivos  = dispositivos.count()
    dispositivos_ativos = dispositivos.filter(is_ativo=True).count()
    total_leituras      = LeituraLog.objects.count()
    leituras_sucesso    = LeituraLog.objects.filter(sucesso_identificacao=True).count()
    leituras_falha      = LeituraLog.objects.filter(sucesso_identificacao=False).count()

    leituras = LeituraLog.objects.select_related("dispositivo", "item_associado").order_by("-timestamp")[:30]

    # Tags lidas mas sem item cadastrado (deduplicadas por UID, mais recente de cada)
    tags_pendentes_raw = (
        LeituraLog.objects
        .filter(sucesso_identificacao=False)
        .select_related("dispositivo")
        .order_by("rfid_uid", "-timestamp")
    )
    # Pega apenas a leitura mais recente de cada UID único
    seen_uids = set()
    tags_pendentes = []
    for log in tags_pendentes_raw:
        uid = log.rfid_uid.upper()
        if uid not in seen_uids:
            seen_uids.add(uid)
            tags_pendentes.append(log)
    tags_pendentes.sort(key=lambda x: x.timestamp, reverse=True)

    return render(request, "mainpage/iot_dashboard.html", {
        "dispositivos": dispositivos,
        "total_dispositivos": total_dispositivos,
        "dispositivos_ativos": dispositivos_ativos,
        "total_leituras": total_leituras,
        "leituras_sucesso": leituras_sucesso,
        "leituras_falha": leituras_falha,
        "leituras": leituras,
        "tags_pendentes": tags_pendentes,
        "total_tags_pendentes": len(tags_pendentes),
    })


@login_required(login_url="login")
def iot_device_detail(request, device_id):
    from iot.models import Dispositivo, LeituraLog
    from django.core.paginator import Paginator

    dispositivo    = get_object_or_404(Dispositivo, id=device_id)
    total_leituras = dispositivo.leituras.count()
    leituras_sucesso = dispositivo.leituras.filter(sucesso_identificacao=True).count()
    leituras_falha   = dispositivo.leituras.filter(sucesso_identificacao=False).count()
    taxa_sucesso     = round(leituras_sucesso / total_leituras * 100) if total_leituras else 0

    leituras_qs = dispositivo.leituras.select_related("item_associado").order_by("-timestamp")
    paginator   = Paginator(leituras_qs, 20)
    page        = request.GET.get("page", 1)
    leituras    = paginator.get_page(page)

    return render(request, "mainpage/iot_device_detail.html", {
        "dispositivo": dispositivo,
        "total_leituras": total_leituras,
        "leituras_sucesso": leituras_sucesso,
        "leituras_falha": leituras_falha,
        "taxa_sucesso": taxa_sucesso,
        "leituras": leituras,
    })


@login_required(login_url="login")
@require_POST
def iot_create_device(request):
    from iot.models import Dispositivo

    nome       = (request.POST.get("nome") or "").strip()
    token_auth = (request.POST.get("token_auth") or "").strip()

    if not nome or not token_auth:
        messages.error(request, "Nome e token são obrigatórios.")
        return redirect("iot_dashboard")

    if Dispositivo.objects.filter(token_auth=token_auth).exists():
        messages.error(request, "Esse token já está em uso. Gere um novo.")
        return redirect("iot_dashboard")

    Dispositivo.objects.create(nome=nome, token_auth=token_auth)
    messages.success(request, f'Dispositivo "{nome}" cadastrado com sucesso!')
    return redirect("iot_dashboard")


@login_required(login_url="login")
@require_POST
def iot_toggle_device(request, device_id):
    from iot.models import Dispositivo

    dispositivo = get_object_or_404(Dispositivo, id=device_id)
    dispositivo.is_ativo = not dispositivo.is_ativo
    dispositivo.save(update_fields=["is_ativo"])
    estado = "ativado" if dispositivo.is_ativo else "desativado"
    messages.success(request, f'Dispositivo "{dispositivo.nome}" {estado}.')
    return redirect("iot_device_detail", device_id=device_id)


@login_required(login_url="login")
@require_POST
def iot_delete_device(request, device_id):
    from iot.models import Dispositivo
    dispositivo = get_object_or_404(Dispositivo, id=device_id)
    nome = dispositivo.nome
    dispositivo.delete()
    messages.success(request, f'Dispositivo "{nome}" excluído.')
    return redirect("iot_dashboard")


@login_required(login_url="login")
def iot_logs(request):
    """Tela de todos os logs de leitura com paginação."""
    from iot.models import LeituraLog
    from django.core.paginator import Paginator

    logs_qs  = LeituraLog.objects.select_related("dispositivo", "item_associado").order_by("-timestamp")
    paginator = Paginator(logs_qs, 40)
    page     = request.GET.get("page", 1)
    leituras = paginator.get_page(page)

    return render(request, "mainpage/iot_logs.html", {
        "leituras": leituras,
        "total": logs_qs.count(),
    })

# -----------------------------
# Páginas Legais e Institucionais
# -----------------------------
def privacy(request):
    return render(request, "mainpage/privacy.html")

def terms(request):
    return render(request, "mainpage/terms.html")