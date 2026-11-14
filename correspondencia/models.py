from django.db import models


class ParGabarito(models.Model):
    """Liga cada item perdido ao item achado correto."""

    perdido = models.OneToOneField("items.Item", on_delete=models.CASCADE, related_name="gabarito")
    achado = models.ForeignKey("items.Item", on_delete=models.CASCADE, related_name="+")
    variacao = models.CharField(max_length=20)       # nenhuma, sinonimo, erro_digitacao ou sem_acento
    objeto_parecido = models.BooleanField()          # há outro objeto do mesmo tipo no catálogo?

    def __str__(self):
        return f"Gabarito #{self.id}: {self.perdido.titulo} -> {self.achado.titulo} ({self.variacao})"
