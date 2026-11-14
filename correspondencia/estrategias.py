import imagehash
import numpy as np
from PIL import Image
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mainpage.views import _calcular_match_score

from .texto import normalizar, texto_do_item

# Os mesmos status que o FIND usa para buscar candidatos (confira na view que você leu).
STATUS_CANDIDATOS = ["achado", "pendente_confirmacao", "confirmado"]


class Estrategia:
    """Forma comum de todas as estratégias."""

    nome = ""

    def preparar(self, candidatos):
        """Recebe todos os candidatos uma única vez (ex.: montar a matriz do TF-IDF)."""
        self.candidatos = list(candidatos)

    def pontuar(self, perdido):
        """Devolve {id_do_candidato: pontuação de 0 a 1}."""
        raise NotImplementedError


class B0(Estrategia):
    nome = "B0"

    def pontuar(self, perdido):
        # A pontuação do FIND vai de 0 a 100; aqui ela é dividida por 100.
        return {c.id: _calcular_match_score(perdido, c) / 100 for c in self.candidatos}


class T1(Estrategia):
    nome = "T1"

    def preparar(self, candidatos):
        super().preparar(candidatos)
        # Cada texto vira um vetor com o "peso" de cada trecho de 3 a 5 letras.
        self.vetorizador = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        textos = [normalizar(texto_do_item(c)) for c in self.candidatos]
        self.matriz = self.vetorizador.fit_transform(textos)

    def pontuar(self, perdido):
        consulta = self.vetorizador.transform([normalizar(texto_do_item(perdido))])
        similaridades = cosine_similarity(consulta, self.matriz)[0]  # de 0 a 1
        return {c.id: float(s) for c, s in zip(self.candidatos, similaridades)}


def histograma(item):
    """Histograma de cor HSV da foto do item, normalizado para somar 1.

    Usa o mesmo método do FIND (PIL .histogram(), 768 bins: 256 H + 256 S + 256 V).
    """
    with item.imagem.open("rb") as arquivo:
        img = Image.open(arquivo)
        img.load()
        hsv = img.convert("HSV")
        hist = np.array(hsv.histogram(), dtype=np.float32)
    soma = hist.sum()
    if soma > 0:
        hist /= soma
    return hist


class V(Estrategia):
    nome = "V"

    def preparar(self, candidatos):
        super().preparar(candidatos)
        # Hash e histograma de cada candidato com foto, calculados uma única vez.
        self.fotos = {}
        for c in self.candidatos:
            if c.imagem and c.image_hash:
                self.fotos[c.id] = (imagehash.hex_to_hash(c.image_hash), histograma(c))

    def pontuar(self, perdido):
        if not (perdido.imagem and perdido.image_hash):
            return {c.id: 0.0 for c in self.candidatos}
        hash_p = imagehash.hex_to_hash(perdido.image_hash)
        hist_p = histograma(perdido)
        pontuacoes = {}
        for c in self.candidatos:
            if c.id not in self.fotos:
                pontuacoes[c.id] = 0.0  # achado sem foto não pode ser confirmado pela imagem
                continue
            hash_c, hist_c = self.fotos[c.id]
            nota_hash = 1 - (hash_p - hash_c) / hash_p.hash.size  # 1 - Hamming / 256
            nota_hist = float(np.minimum(hist_p, hist_c).sum())    # interseção de histogramas
            pontuacoes[c.id] = 0.5 * nota_hash + 0.5 * nota_hist
        return pontuacoes


class F(Estrategia):

    def __init__(self, usar_foto=True):
        self.usar_foto = usar_foto
        self.nome = "F" if usar_foto else "F (sem foto)"
        self.t1 = T1()
        self.v = V()

    def preparar(self, candidatos):
        super().preparar(candidatos)
        self.t1.preparar(self.candidatos)
        if self.usar_foto:
            self.v.preparar(self.candidatos)

    def partes(self, perdido):
        """Devolve, para cada candidato, as três partes da pontuação e a pontuação final."""
        texto = self.t1.pontuar(perdido)
        imagem = self.v.pontuar(perdido) if self.usar_foto else None
        resultado = {}
        for c in self.candidatos:
            categoria = 1.0 if c.categoria_id == perdido.categoria_id else 0.0
            if imagem is None:
                final = (0.6 * texto[c.id] + 0.1 * categoria) / 0.7
            else:
                final = 0.6 * texto[c.id] + 0.3 * imagem[c.id] + 0.1 * categoria
            resultado[c.id] = {
                "texto": texto[c.id],
                "imagem": imagem[c.id] if imagem is not None else None,
                "categoria": categoria,
                "final": final,
            }
        return resultado

    def pontuar(self, perdido):
        return {id_: p["final"] for id_, p in self.partes(perdido).items()}
