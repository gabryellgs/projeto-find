"""Validação de arquivos enviados pelo usuário (upload de imagens).

Não confia no `content-type` declarado pelo cliente no multipart/form-data
(trivialmente falsificável) — abre o arquivo com Pillow e verifica que os
bytes reais formam uma imagem raster válida antes de aceitar o upload.

Nota: python-magic/libmagic foi avaliado e descartado aqui — em ambientes
sem libmagic instalada (ex.: dev no Windows) `import magic` trava
indefinidamente em vez de falhar rápido, o que é um risco inaceitável para
uma verificação executada a cada request. Pillow já é dependência obrigatória
do projeto e é suficiente para rejeitar SVG/HTML/executáveis disfarçados de
imagem.
"""
from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE_MB = 5

ALLOWED_IMAGE_FORMATS = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'WEBP': 'image/webp',
    'GIF': 'image/gif',
}


def validate_image_file(uploaded_file, max_size_mb=MAX_IMAGE_SIZE_MB):
    """Valida que o arquivo enviado é realmente uma imagem raster permitida.

    Levanta ValidationError se o arquivo for grande demais ou não for
    reconhecido como um dos formatos de imagem permitidos. Retorna o
    mime-type detectado.
    """
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"Arquivo muito grande (máx. {max_size_mb}MB).")

    from PIL import Image, UnidentifiedImageError

    uploaded_file.seek(0)
    try:
        with Image.open(uploaded_file) as img:
            img.verify()
            formato = img.format
    except (UnidentifiedImageError, OSError, ValueError):
        formato = None
    finally:
        uploaded_file.seek(0)

    detected_type = ALLOWED_IMAGE_FORMATS.get(formato)
    if not detected_type:
        raise ValidationError("Tipo de arquivo não permitido. Envie uma imagem JPEG, PNG, WEBP ou GIF.")

    return detected_type
