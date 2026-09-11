# 🔍 Plataforma FIND

**Find** é um ecossistema centralizado para gestão de achados e perdidos em ambientes institucionais. Integra interfaces web, mobile e IoT para oferecer rastreamento de itens em tempo real e comunicação fluida entre os usuários.

---

## 🏗️ Arquitetura e Ecossistema

A plataforma é composta por três componentes integrados:

1. **Plataforma Web (SaaS):** Painel administrativo responsivo construído com Django, com UI em Glassmorphism e roteamento baseado em permissões para administradores e bolsistas.
2. **Aplicativo Mobile:** Aplicação cross-platform em React Native com experiência nativa e gestos fluidos.
3. **Integração IoT:** Integração com hardware ESP32 e tecnologia RFID para validação e leitura de ativos em tempo real.

---

## 🛠️ Stack Tecnológica

**Backend**
| Tecnologia | Versão |
|-----------|--------|
| Python | 3.12+ |
| Django | 6.0.3 |
| Django REST Framework | 3.15.2 |
| Django Channels (WebSocket) | 4.1.0 |
| Daphne (ASGI Server) | 4.2.2 |
| Gunicorn (WSGI Server) | 26.0.0 |
| Simple JWT | 5.5.0 |
| Pillow (Imagens) | 12.1.1 |
| python-magic (MIME) | 0.4.27 |

**Banco de Dados e Cache**
| Serviço | Uso |
|---------|-----|
| MySQL 8.4 | Banco principal (produção/Docker) |
| SQLite | Banco de desenvolvimento local |
| Redis 7 | Cache e WebSocket (Django Channels) |

**Frontend (Web)**
- HTML5, CSS3, JavaScript (ES6+)
- Bootstrap 5 com UI customizada
- Mapas interativos via Leaflet.js
- Cloudinary para armazenamento de mídias

**DevOps**
- Docker & Docker Compose
- Deploy contínuo via Render

---

## 📋 Pré-requisitos

### Requisitos Gerais
- [Git](https://git-scm.com/download/win)
- [Python 3.12+](https://www.python.org/downloads/)
- [Docker Desktop para Windows](https://www.docker.com/products/docker-desktop/) *(apenas para instalação com Docker)*

### ⚠️ Atenção — Dependência no Windows (`python-magic`)
O pacote `python-magic` requer uma DLL nativa. No Windows, instale também:

```powershell
pip install python-magic-bin
```

> Essa dependência substitui a necessidade de `libmagic1` do Linux.

---

## 🚀 Instalação e Configuração

### Opção A: Docker (Recomendado)

> Sobe automaticamente o banco MySQL, Redis e a aplicação Django com um único comando.

**Passo 1 — Clone o repositório**
```powershell
git clone https://github.com/gabryellgs/projeto-find.git
cd projeto-find
```

**Passo 2 — Crie o arquivo de variáveis de ambiente**

Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados (preenchido automaticamente pelo docker-compose)
DB_NAME=find_db
DB_USER=find_user
DB_PASSWORD=find_password
DB_HOST=db
DB_PORT=3306

# Redis
REDIS_URL=redis://redis:6379/1

# Cloudinary (opcional — para armazenamento de mídias em nuvem)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

**Passo 3 — Construa e suba os containers**
```powershell
docker-compose build web
docker-compose up -d
```

**Passo 4 — Acesse a aplicação**

Abra o navegador em: [http://localhost:8000](http://localhost:8000)

**Comandos úteis do Docker**
```powershell
# Ver logs em tempo real
docker-compose logs -f web

# Parar todos os containers
docker-compose down

# Parar e remover volumes (banco de dados)
docker-compose down -v

# Executar comandos dentro do container
docker-compose exec web python manage.py createsuperuser
```

---

### Opção B: Ambiente Local (Windows)

> Ideal para desenvolvimento sem Docker. Usa SQLite como banco de dados.

**Passo 1 — Clone o repositório**
```powershell
git clone https://github.com/gabryellgs/projeto-find.git
cd projeto-find
```

**Passo 2 — Crie e ative o ambiente virtual**
```powershell
python -m venv venv
venv\Scripts\activate
```

> Após ativar, o terminal exibirá `(venv)` no início da linha.

**Passo 3 — Instale as dependências**
```powershell
pip install -r requirements.txt
pip install python-magic-bin
```

**Passo 4 — Configure as variáveis de ambiente**

Crie o arquivo `.env` na raiz do projeto:
```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

> Em desenvolvimento local, o Django usará SQLite automaticamente (sem necessidade de MySQL).

**Passo 5 — Execute as migrações e popule dados iniciais**
```powershell
python manage.py migrate
python manage.py criar_categorias
python manage.py gerar_hashes
```

**Passo 6 — Colete os arquivos estáticos**
```powershell
python manage.py collectstatic --noinput
```

**Passo 7 — (Opcional) Crie um superusuário**
```powershell
python manage.py createsuperuser
```

**Passo 8 — Inicie o servidor de desenvolvimento**
```powershell
python manage.py runserver
```

Acesse em: [http://localhost:8000](http://localhost:8000)

---

## 🧪 Executando os Testes

O projeto utiliza **pytest** com **pytest-django**.

```powershell
# Ativar o ambiente virtual (se ainda não estiver ativo)
venv\Scripts\activate

# Rodar todos os testes
pytest

# Com saída detalhada
pytest -v

# Com relatório de cobertura de código
pytest --cov=. --cov-report=html
# O relatório será gerado em: htmlcov/index.html

# Rodar testes de um app específico
pytest accounts/ -v
pytest items/ -v
pytest iot/ -v
pytest chats/ -v

# Rodar uma classe de teste específica
pytest iot/tests/test_api.py::TestIotScanAutenticacao -v
```

---

## ☁️ Deploy

A aplicação está configurada para deploy em plataformas PaaS (Render, Heroku, etc.).

1. Conecte o repositório GitHub ao seu serviço no Render.
2. Selecione o runtime **Docker**.
3. O `Dockerfile` e o `start.sh` cuidam automaticamente de: `collectstatic`, configuração WSGI/ASGI e migrações.

---

## 🔐 Segurança e Conformidade

- **LGPD/GDPR:** Gerenciamento de consentimento de cookies integrado.
- **Controle de Acesso:** RBAC (Role-Based Access Control) separando permissões de administradores, bolsistas e usuários comuns.
- **Proteção de Dados:** Tokens CSRF obrigatórios, cookies seguros e queries parametrizadas contra injeção SQL.
- **Autenticação:** JWT (access + refresh token) e suporte a OAuth2 com Google.

---

## 📁 Estrutura do Projeto

```
projeto-find/
├── accounts/        # Usuários, perfis e autenticação
├── chats/           # Sistema de mensagens e WebSocket
├── items/           # Gerenciamento de itens achados/perdidos
├── iot/             # Integração RFID e dispositivos IoT
├── mainpage/        # Página principal e rotas públicas
├── find/            # Configurações do projeto Django
├── templates/       # Templates HTML globais
├── media/           # Arquivos de mídia (uploads)
├── conftest.py      # Configuração global do pytest
├── pytest.ini       # Configuração do pytest
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

*Plataforma FIND — Licença Proprietária. Todos os direitos reservados.*
