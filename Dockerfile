# ─────────────────────────────────────────────────────────────
#  Find – Dockerfile
#  Imagem de produção: Python 3.12 slim + dependências nativas
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ─── Dependências do sistema (mysqlclient, pillow, python-magic) ───
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    libmagic1 \
    libmagic-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# ─── Dependências Python ───────────────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# ─── Código da aplicação ───────────────────────────────────────
COPY . .

# ─── Coleta de arquivos estáticos ─────────────────────────────
RUN python manage.py collectstatic --noinput

# ─── Porta exposta ─────────────────────────────────────────────
EXPOSE 8000

# ─── Entrypoint padrão (produção com Gunicorn) ─────────────────
CMD ["bash", "start.sh"]
