import string
import unicodedata

from nltk.corpus import stopwords


def tirar_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


STOPWORDS = {tirar_acentos(p) for p in stopwords.words("portuguese")}


def normalizar(texto):
    """Minúsculas, sem acentos, sem pontuação e sem stopwords."""
    texto = tirar_acentos(texto.lower())
    texto = texto.translate(str.maketrans(string.punctuation, " " * len(string.punctuation)))
    return " ".join(p for p in texto.split() if p not in STOPWORDS)


def texto_do_item(item):
    return f"{item.titulo} {item.descricao}"

