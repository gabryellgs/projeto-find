"""
Django settings para o projeto Find.
Configurado para produção no Render + banco MySQL no Railway.
"""
from datetime import timedelta
from pathlib import Path
import os

from decouple import config, Csv

# ─── Caminhos ─────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Segurança ────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-only')
DEBUG = config('DEBUG', default=False, cast=bool)

# Inclui o domínio de produção conhecido (find.ifrn.edu.br, usado em items/models.py
# para gerar URLs de QR Code) no default — assim, mesmo que a env var ALLOWED_HOSTS
# não esteja configurada no Render, o domínio real continua funcionando sem
# precisar do curinga "*" (que aceitava qualquer Host header).
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='localhost,127.0.0.1,find.ifrn.edu.br,www.find.ifrn.edu.br',
    cast=Csv(),
)
# Render injeta este env automaticamente no deploy
RENDER_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_HOSTNAME)

# ─── Apps instalados ──────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # terceiros
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    # 'whitenoise.runserver_nostatic', (Removido para permitir hot-reload do CSS em dev)
    # apps do projeto (modular)
    'accounts.apps.AccountsConfig',
    'items.apps.ItemsConfig',
    'chats.apps.ChatsConfig',
    'iot.apps.IotConfig',
    # app principal
    'mainpage.apps.MainpageConfig',
    # allauth (login social)
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # Apple OAuth removido — não configurado
]

SITE_ID = 1

# ─── Middleware ───────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # logo após Security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # allauth
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'find.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.user_roles',
            ],
        },
    },
]

WSGI_APPLICATION = 'find.wsgi.application'
ASGI_APPLICATION = 'find.asgi.application'

if os.getenv("RENDER"):
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(config("REDIS_URL", default="redis://127.0.0.1:6379/1"))],
            },
        },
    }
else:
    # Dev local: sem necessidade de Redis
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

# ─── Banco de dados ───────────────────────────────────────────
if os.getenv("RENDER"):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='find_db'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'connect_timeout': 10,
            },
            'CONN_MAX_AGE': 60,
        }
    } 
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ─── CORS ─────────────────────────────────────────────────────
# Apps nativos (mobile) não são afetados por CORS — é uma restrição imposta
# pelo navegador, não pelo cliente HTTP. Só front-ends web (Vite dev/produção)
# precisam estar aqui. CORS_ALLOW_ALL_ORIGINS + CORS_ALLOW_CREDENTIALS juntos
# permitiam que qualquer site na internet enviasse requisições autenticadas
# com os cookies de sessão do usuário — por isso a lista explícita abaixo.
_WEB_TRUSTED_ORIGINS = config(
    'WEB_TRUSTED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173,https://projeto-find.onrender.com',
    cast=Csv(),
)
CORS_ALLOWED_ORIGINS = _WEB_TRUSTED_ORIGINS
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = _WEB_TRUSTED_ORIGINS

# ─── DRF + JWT ────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_THROTTLE_RATES': {
        # Escopos usados por views específicas via @throttle_classes;
        # não afeta o restante da API (sem DEFAULT_THROTTLE_CLASSES global).
        # iot-scan: deliberadamente generoso (não sabemos a frequência real de
        # scan do hardware físico, nem se múltiplos leitores share o mesmo IP
        # público atrás do NAT da instituição) — existe só para conter um
        # flood extremo, não para limitar o uso normal do RFID.
        'iot-scan': '1000/minute',
        'visual-search': '10/minute',
    },
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# ─── Validação de senhas ──────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internacionalização ──────────────────────────────────────
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Fortaleza'
USE_I18N = True
USE_TZ = True

# ─── Arquivos estáticos (WhiteNoise) ──────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'mainpage', 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Storage de mídia (salva no banco de dados) ───────────────
STORAGES = {
    'default': {
        'BACKEND': 'find.storage.DatabaseStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# ─── E-mail ───────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = f'Find App <{EMAIL_HOST_USER}>'

# ─── Backends de Autenticação ─────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# ─── Configurações Allauth ────────────────────────────────────
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_REQUIRED = True
SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APPS': [
            {
                'client_id': config('GOOGLE_CLIENT_ID', default=''),
                'secret': config('GOOGLE_CLIENT_SECRET', default=''),
                'key': ''
            }
        ]
    }
}

# ─── Gemini API (Busca Visual Inteligente) ──────────────────────
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')

# Nota: a autenticação de dispositivos IoT (ESP32/RFID) usa o token por
# dispositivo em Dispositivo.token_auth (banco de dados), não um token
# global fixo — ver iot/api/views.py::api_iot_scan.

# ─── Hardening de produção (Render) ────────────────────────────
if os.getenv("RENDER"):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7  # 7 dias
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
