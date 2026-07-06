from django.contrib import admin
from .models import Chat, Mensagem


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "criado_por", "dono_item", "status", "atualizado_em")
    list_filter = ("status",)
    search_fields = ("criado_por__username", "dono_item__username", "item__titulo")


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "remetente", "data_envio", "lida")
    list_filter = ("lida", "tipo")
    search_fields = ("conteudo", "remetente__username")
