from pathlib import Path

from PIL import Image

FOTOS = Path(__file__).resolve().parents[1] / "dados" / "fotos"


def test_foto_tratada_nao_tem_exif():
    """Confere que as fotos tratadas não guardam metadados EXIF (privacidade)."""
    fotos = list(FOTOS.glob("*.jpg"))
    if not fotos:
        import pytest
        pytest.skip("Nenhuma foto tratada encontrada em dados/fotos/")
    for foto in fotos[:5]:  # confere as 5 primeiras
        exif = Image.open(foto).getexif()
        assert len(exif) == 0, f"{foto.name} ainda tem EXIF: {dict(exif)}"


def test_foto_tratada_tamanho_maximo_800():
    """Confere que o lado maior de cada foto tratada tem no máximo 800 px."""
    fotos = list(FOTOS.glob("*.jpg"))
    if not fotos:
        import pytest
        pytest.skip("Nenhuma foto tratada encontrada em dados/fotos/")
    for foto in fotos[:5]:
        img = Image.open(foto)
        assert max(img.size) <= 800, f"{foto.name} tem {img.size}, maior que 800"

