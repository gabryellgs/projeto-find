from django.core.management.base import BaseCommand

from correspondencia.estrategias import F, STATUS_CANDIDATOS
from items.models import Item


class Command(BaseCommand):
    help = "Mostra as 6 sugestões da F para um item perdido."

    def add_arguments(self, parser):
        parser.add_argument("perdido_id", type=int)

    def handle(self, *args, **opcoes):
        perdido = Item.objects.get(id=opcoes["perdido_id"])
        f = F()
        f.preparar(Item.objects.filter(status__in=STATUS_CANDIDATOS))
        partes = f.partes(perdido)
        itens = {c.id: c for c in f.candidatos}
        correto = perdido.gabarito.achado_id

        self.stdout.write(f"PERDIDO: {perdido.titulo} | {perdido.descricao}\n")
        melhores = sorted(partes, key=lambda id_: (-partes[id_]["final"], id_))[:6]
        for posicao, id_ in enumerate(melhores, start=1):
            p = partes[id_]
            marca = "  <-- CORRETO" if id_ == correto else ""
            img_str = f"{p['imagem']:.2f}" if p["imagem"] is not None else "N/A"
            self.stdout.write(
                f"{posicao}. {itens[id_].titulo:<30} final {p['final']:.2f} | "
                f"texto {p['texto']:.2f} | imagem {img_str} | categoria {p['categoria']:.0f}{marca}"
            )

