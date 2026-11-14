from pathlib import Path

from django.core.management.base import BaseCommand
from PIL import Image, ImageOps

DADOS = Path(__file__).resolve().parents[2] / "dados"


class Command(BaseCommand):
    help = "Gira, reduz para 800 px e remove os metadados das fotos."

    def handle(self, *args, **opcoes):
        destino = DADOS / "fotos"
        destino.mkdir(exist_ok=True)
        for origem in sorted((DADOS / "fotos_originais").glob("*.jpg")):
            imagem = ImageOps.exif_transpose(Image.open(origem)).convert("RGB")  # 1. corrige a rotação
            imagem.thumbnail((800, 800))                                          # 2. lado maior com 800 px
            imagem.save(destino / origem.name, "JPEG", quality=85)                # 3. salva sem o EXIF
            self.stdout.write(f"ok {origem.name}")
