from django.contrib import admin
from .models import Item, Categoria, ArquivoMidia, AcaoLog, Notificacao

admin.site.register(Item)
admin.site.register(Categoria)


@admin.register(ArquivoMidia)
class ArquivoMidiaAdmin(admin.ModelAdmin):
    # Sem "conteudo" (BinaryField) no list_display/fields: evita carregar o
    # blob inteiro de cada imagem ao simplesmente abrir a listagem do admin.
    list_display = ("nome", "content_type", "tamanho", "criado_em")
    search_fields = ("nome", "content_type")
    readonly_fields = ("nome", "content_type", "tamanho", "criado_em")
    exclude = ("conteudo",)


@admin.register(AcaoLog)
class AcaoLogAdmin(admin.ModelAdmin):
    list_display = ("bolsista", "acao", "item", "timestamp", "ip_origem")
    list_filter = ("acao",)
    search_fields = ("bolsista__username", "item__titulo", "observacao")


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "titulo", "lida", "criado_em")
    list_filter = ("lida",)
    search_fields = ("usuario__username", "titulo", "mensagem")
