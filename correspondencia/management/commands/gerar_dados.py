import csv
import json
import random
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from correspondencia.models import ParGabarito
from items.models import Categoria, Item

DADOS = Path(__file__).resolve().parents[2] / "dados"
# Cores dos distratores: palavras que não mudam com o gênero ("mochila verde", "carregador verde").
CORES_TROCA = ["azul", "verde", "cinza", "rosa", "marrom", "bege", "laranja", "vinho"]


def tirar_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def tem_acento(obj):
    texto = f"{obj['tipo']} {obj['cor']} {obj['detalhe']}"
    return tirar_acentos(texto) != texto


def errar_digitacao(texto, rng):
    """Troca, apaga ou repete uma letra em uma palavra com 4 letras ou mais."""
    palavras = texto.split()
    candidatas = [i for i, p in enumerate(palavras) if len(p) >= 4]
    while True:
        i = rng.choice(candidatas)
        p = palavras[i]
        pos = rng.randrange(1, len(p) - 1)
        tipo = rng.choice(["troca", "falta", "sobra"])
        if tipo == "troca":
            nova = p[:pos] + p[pos + 1] + p[pos] + p[pos + 2:]
        elif tipo == "falta":
            nova = p[:pos] + p[pos + 1:]
        else:
            nova = p[:pos] + p[pos] + p[pos:]
        if nova != p:  # "garrafa" trocando "rr" continua igual; sorteia de novo
            palavras[i] = nova
            return " ".join(palavras)


def maiuscula(texto):
    return texto[0].upper() + texto[1:] if texto else texto


def texto_achado(obj):
    titulo = maiuscula(f"{obj['tipo']} {obj['cor']}")
    partes = [f"{titulo}."]
    if obj["marca"]:
        partes.append(f"Marca: {obj['marca']}.")
    if obj["detalhe"]:
        partes.append(f"{maiuscula(obj['detalhe'])}.")
    return titulo[:45], " ".join(partes)[:200]


def texto_perdido(obj, tipo):
    titulo = maiuscula(f"{tipo} {obj['cor']}")
    partes = [f"Procuro {tipo} {obj['cor']}."]
    if obj["marca"]:
        partes.append(f"É da marca {obj['marca']}.")
    if obj["detalhe"]:
        partes.append(f"Detalhe: {obj['detalhe']}.")
    return titulo[:45], " ".join(partes)[:200]


def criar_item(titulo, descricao, status, categoria, local, usuario, foto=None):
    item = Item(
        titulo=titulo,
        descricao=descricao,
        status=status,
        categoria=categoria,
        local=local[:45],
        usuario=usuario,
        data=date.today(),
    )
    if foto and foto.exists():
        # O próprio FIND grava a imagem no banco e calcula o image_hash no save().
        item.imagem.save(foto.name, ContentFile(foto.read_bytes()), save=False)
    item.save()
    return item


class Command(BaseCommand):
    help = "Cria os perdidos, os achados e o gabarito do experimento."

    def add_arguments(self, parser):
        parser.add_argument("--semente", type=int, default=42)

    def handle(self, *args, **opcoes):
        # 1. Segurança: nunca roda fora do ambiente local.
        if not settings.DEBUG:
            raise CommandError("Este comando só roda com DEBUG=True.")

        # 2. Um único sorteador para o comando inteiro. Nunca use random.choice direto.
        rng = random.Random(opcoes["semente"])

        # 3. Lê os arquivos de dados.
        with open(DADOS / "catalogo.csv", encoding="utf-8-sig") as arquivo:
            catalogo = list(csv.DictReader(arquivo))
        sinonimos = json.loads((DADOS / "sinonimos.json").read_text(encoding="utf-8"))
        locais = (DADOS / "locais.txt").read_text(encoding="utf-8").splitlines()

        # 4. Apaga só o que este comando criou na rodada anterior (usuários "tcc_").
        Item.objects.filter(usuario__username__startswith="tcc_").delete()
        Usuario = get_user_model()
        dono, _ = Usuario.objects.get_or_create(username="tcc_dono")
        achador, _ = Usuario.objects.get_or_create(username="tcc_achador")

        # 5. Sorteia o grupo de variação de cada objeto, dividindo igualmente.
        #    O grupo "sem_acento" só pode receber objetos que têm acento no texto.
        n = len(catalogo)
        tamanho_grupo = n // 4  # 4 grupos; objetos extras vão para "nenhuma"
        com_acento = [obj["id"] for obj in catalogo if tem_acento(obj)]
        if len(com_acento) < tamanho_grupo:
            raise CommandError(
                f"O catálogo precisa de pelo menos {tamanho_grupo} objetos com acento "
                f"(tem {len(com_acento)})."
            )
        grupo = {id_: "sem_acento" for id_ in rng.sample(com_acento, tamanho_grupo)}
        resto = [obj["id"] for obj in catalogo if obj["id"] not in grupo]
        rng.shuffle(resto)
        outros = ["nenhuma", "sinonimo", "erro_digitacao"]
        grupo.update({id_: outros[i % 3] for i, id_ in enumerate(resto)})
        quantos_do_tipo = Counter(obj["tipo"] for obj in catalogo)

        for obj in catalogo:
            numero = int(obj["id"])
            categoria = Categoria.objects.get(nome=obj["categoria"])
            local = rng.choice(locais)

            # 6. Achado verdadeiro: foto A e texto padrão.
            titulo, descricao = texto_achado(obj)
            achado = criar_item(titulo, descricao, "achado", categoria, local, achador,
                                DADOS / "fotos" / f"{numero:03d}_A.jpg")

            # 7. Perdido: foto B e texto do dono, com a variação do grupo.
            variacao = grupo[obj["id"]]
            tipo = obj["tipo"]
            if variacao == "sinonimo":
                tipo = rng.choice(sinonimos[obj["tipo"]])
            elif variacao == "erro_digitacao":
                tipo = errar_digitacao(tipo, rng)
            titulo, descricao = texto_perdido(obj, tipo)
            if variacao == "sem_acento":
                titulo, descricao = tirar_acentos(titulo), tirar_acentos(descricao)
            perdido = criar_item(titulo, descricao, "perdido", categoria, rng.choice(locais), dono,
                                 DADOS / "fotos" / f"{numero:03d}_B.jpg")

            # 8. Gabarito.
            ParGabarito.objects.create(
                perdido=perdido,
                achado=achado,
                variacao=variacao,
                objeto_parecido=quantos_do_tipo[obj["tipo"]] > 1,
            )

            # 9. Distrator "quase igual": sem foto, com outra cor.
            outra_cor = rng.choice([c for c in CORES_TROCA if c != obj["cor"]])
            titulo, descricao = texto_achado({**obj, "cor": outra_cor})
            criar_item(titulo, descricao, "achado", categoria, rng.choice(locais), achador)

        self.stdout.write(self.style.SUCCESS(
            f"{Item.objects.filter(status='perdido', usuario=dono).count()} perdidos, "
            f"{Item.objects.filter(status='achado', usuario=achador).count()} achados, "
            f"{ParGabarito.objects.count()} pares."
        ))
