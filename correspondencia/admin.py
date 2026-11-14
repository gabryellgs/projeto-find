from django.contrib import admin
from .models import ParGabarito


@admin.register(ParGabarito)
class ParGabaritoAdmin(admin.ModelAdmin):
    list_display = ("perdido", "achado", "variacao", "objeto_parecido")
