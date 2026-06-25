def user_roles(request):
    """
    Context processor para disponibilizar permissões do usuário em todos os templates.
    """
    if not request.user.is_authenticated:
        return {'is_bolsista_user': False, 'is_admin_user': False}
    
    is_admin = request.user.groups.filter(name="Administradores").exists() or request.user.is_staff
    is_bolsista = request.user.groups.filter(name="Bolsistas").exists() or is_admin
    
    # Notificações não lidas
    try:
        from items.models import Notificacao
        notificacoes_nao_lidas = Notificacao.objects.filter(usuario=request.user, lida=False).order_by('-criado_em')
        notificacoes_count = notificacoes_nao_lidas.count()
        notificacoes_recentes = notificacoes_nao_lidas[:5]
    except Exception:
        notificacoes_nao_lidas = []
        notificacoes_count = 0
        notificacoes_recentes = []

    return {
        'is_bolsista_user': is_bolsista,
        'is_admin_user': is_admin,
        'user_notificacoes_count': notificacoes_count,
        'user_notificacoes': notificacoes_recentes,
    }
