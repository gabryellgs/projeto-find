from django.contrib import admin
from .models import Dispositivo, LeituraLog

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'is_ativo', 'criado_em', 'ultima_comunicacao')
    list_filter = ('is_ativo',)
    search_fields = ('nome',)
    readonly_fields = ('token_auth', 'criado_em', 'ultima_comunicacao')

@admin.register(LeituraLog)
class LeituraLogAdmin(admin.ModelAdmin):
    list_display = ('dispositivo', 'rfid_uid', 'sucesso_identificacao', 'timestamp', 'item_associado')
    list_filter = ('sucesso_identificacao', 'timestamp')
    search_fields = ('rfid_uid', 'dispositivo__nome')
    readonly_fields = ('timestamp',)
