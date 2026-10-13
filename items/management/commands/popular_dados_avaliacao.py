import io
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from faker import Faker
from PIL import Image, ImageDraw

from chats.models import Chat, Mensagem
from items.models import Categoria, Item

OBJETOS = [
    "Garrafa térmica azul", "Carregador de celular", "Óculos de grau",
    "Mochila preta", "Chaveiro com três chaves", "Casaco cinza",
    "Fone de ouvido sem fio", "Carteira marrom", "Calculadora científica",
    "Guarda-chuva", "Caderno de anotações", "Crachá de estudante",
]
LOCAIS = ["Biblioteca", "Bloco A - Sala 3", "Cantina", "Laboratório 2", "Quadra", "Auditório"]
MENSAGENS = [
    ("visitante", "Olá! Acho que esse item é meu."),
    ("avaliadora", "Oi! Pode me dizer onde você o perdeu?"),
    ("visitante", "Foi na biblioteca, perto da mesa de estudos."),
    ("avaliadora", "Combina com o que encontrei. Podemos nos encontrar amanhã?"),
]
SENHA = "Avaliacao@2026"


def gerar_imagem(indice, texto):
    imagem = Image.new("RGB", (640, 480), (40 + indice * 13, 120, 160))
    ImageDraw.Draw(imagem).text((40, 220), texto, fill="white")
    buffer = io.BytesIO()
    imagem.save(buffer, format="JPEG")
    return ContentFile(buffer.getvalue())


class Command(BaseCommand):
    help = "Cria usuários, itens e uma conversa fictícios para a avaliação de acessibilidade."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Use este comando apenas no ambiente local (DEBUG=True).")

        fake = Faker("pt_BR")
        Faker.seed(2026)
        User = get_user_model()

        usuarios = {}
        for nome in ["avaliadora", "visitante"]:
            usuario, _ = User.objects.get_or_create(
                username=nome, defaults={"email": f"{nome}@example.com"}
            )
            if not usuario.check_password(SENHA):
                usuario.set_password(SENHA)
                usuario.save()
            usuarios[nome] = usuario

        categorias = list(Categoria.objects.order_by("id"))

        itens = []
        for indice, objeto in enumerate(OBJETOS, start=1):
            # slug fixo, senão o save() gera um aleatório e a URL da P07 muda
            item, _ = Item.objects.update_or_create(
                slug=f"avaliacao-{indice:02d}",
                defaults={
                    "titulo": objeto,
                    "descricao": fake.text(max_nb_chars=150),
                    "status": "perdido" if indice % 2 else "achado",
                    "local": LOCAIS[indice % len(LOCAIS)],
                    "data": date(2026, 10, 1) - timedelta(days=indice),
                    "usuario": usuarios["avaliadora"],
                    "categoria": categorias[indice % len(categorias)] if categorias else None,
                },
            )
            if indice % 3 and not item.imagem:
                item.imagem.save(f"avaliacao_{indice:02d}.jpg", gerar_imagem(indice, objeto))
            itens.append(item)

        chat = Chat.objects.filter(
            item=itens[0], criado_por=usuarios["visitante"], dono_item=usuarios["avaliadora"]
        ).first()
        if chat is None:
            chat = Chat.objects.create(
                item=itens[0], criado_por=usuarios["visitante"], dono_item=usuarios["avaliadora"]
            )

        chat.mensagens.all().delete()
        for remetente, texto in MENSAGENS:
            Mensagem.objects.create(chat=chat, remetente=usuarios[remetente], conteudo=texto, lida=True)

        self.stdout.write(self.style.SUCCESS("Dados fictícios criados."))
        self.stdout.write(f"P07 e P13: /item/{itens[0].slug}/")
        self.stdout.write(f"P10: /chats/{chat.id}/")
        self.stdout.write(f"Login: avaliadora@example.com ou visitante@example.com, senha {SENHA}")
