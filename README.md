<div align="center">
  <img src="https://raw.githubusercontent.com/seu-usuario/Find-sitema/main/projeto_find/mainpage/static/mainpage/img/logo-find.png" alt="Find Logo" width="120" style="border-radius: 12px;"/>
  <h1>FIND - Achados e Perdidos</h1>
  <p><strong>Plataforma SaaS Completa para Gestão de Itens Perdidos, App Mobile e Integração IoT (RFID)</strong></p>
</div>

---

## 📌 Sobre o Projeto

O **FIND** não é apenas um site de achados e perdidos; é um ecossistema completo de gestão inteligente de itens voltado para o ambiente acadêmico/institucional (como a COPAC do IFRN). Ele conecta de forma rápida quem perdeu algo com quem encontrou, automatizando fluxos e garantindo segurança na devolução.

### 🌟 Destaques do Ecossistema
- **Plataforma Web (SaaS):** Design premium moderno (*Glassmorphism*, *Baby Blue Palette*), painéis dinâmicos para administradores e fluxo gamificado para bolsistas.
- **Mobile App:** Aplicativo responsivo que espelha perfeitamente a lógica da web, trazendo a experiência nativa (*Bottom Navigation*, *Swipe Cards*) para o smartphone do usuário.
- **Integração IoT (Hardware):** Leitura de cartões e itens via RFID (ESP32) integrados de forma nativa ao banco de dados e dashboard web para inventário em tempo real.
- **Chat e Notificações:** Comunicação segura e direta entre o dono do item e quem o encontrou/registrou.

---

## 🛠️ Tecnologias Utilizadas

**Backend & Web:**
- Python 3.12 + **Django 5.0** (Framework Web e ORM)
- Autenticação avançada (Google OAuth2 integrada)
- Banco de Dados: SQLite (Dev) / PostgreSQL (Produção)
- Gunicorn (Servidor WSGI)

**Frontend:**
- HTML5, CSS3, JavaScript Vanilla
- Bootstrap 5 (Customizado)
- Swiper.js (Carrosséis de cards de itens)
- Leaflet.js (Mapas interativos de localização de perdas)
- Estilização SaaS Premium (Translucidez, Glassmorphism, Micro-interações)

**DevOps & Infra:**
- Docker & Docker Compose
- Render (PaaS Deployment Automático)
- Integração CI/CD nativa

---

## 🚀 Como Executar o Projeto

A maneira mais rápida e garantida de executar o projeto na sua máquina (ou em qualquer servidor) é utilizando o **Docker**. O sistema já vem com tudo mastigado para subir automaticamente.

### 🐳 1. Rodando com Docker (Recomendado)

Certifique-se de ter o [Docker](https://docs.docker.com/get-docker/) e o [Docker Compose](https://docs.docker.com/compose/install/) instalados na sua máquina.

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/SEU_USUARIO/Find-sitema.git
   cd Find-sitema/projeto_find
   ```

2. **Suba os containers da aplicação:**
   ```bash
   docker-compose build web
   docker-compose up -d web
   ```

3. **Acesse a aplicação no navegador:**
   - http://localhost:8000

*O Docker irá instalar o Python, instalar os `requirements.txt`, preparar o banco de dados e aplicar os arquivos estáticos automaticamente usando o arquivo `start.sh`.*

---

### 💻 2. Rodando Localmente (Sem Docker)

Caso prefira rodar diretamente no seu ambiente Python local para desenvolvimento:

1. **Crie e ative um ambiente virtual:**
   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate  # No Windows: .venv\Scripts\activate
   ```

2. **Instale as dependências e o suporte para o Magic (reconhecimento de imagens):**
   ```bash
   # Dependências do sistema (Linux/Ubuntu)
   sudo apt-get install libmagic1 default-libmysqlclient-dev
   
   # Instale os pacotes Python
   pip install -r requirements.txt
   ```

3. **Gere os arquivos estáticos e rode as migrações do Banco:**
   ```bash
   python manage.py collectstatic --noinput
   python manage.py migrate
   python manage.py criar_categorias
   ```

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver
   ```
   Acesse: http://127.0.0.1:8000

---

## ☁️ Deploy no Render

Este repositório está pronto para deploy contínuo (CI/CD) em plataformas como o **Render**.

1. Crie um Web Service no Render conectado a este repositório do GitHub.
2. Defina o **Environment** como `Docker` ou use o comando nativo se escolher `Python 3` (Build Command: `./start.sh`, Start Command: `gunicorn find.wsgi:application`).
3. O script `start.sh` interno garante que as migrações de banco e a coleta dos seus arquivos estáticos (CSS atualizados) sejam feitas de forma 100% autônoma a cada Push.

---

## 🔒 Segurança e LGPD

- Banner flutuante nativo e gerenciador de cookies implementados.
- Políticas de Privacidade e Termos de Uso documentados de acordo com os padrões legais (gov.br).
- Rotas sensíveis (como gestão IoT e painéis administrativos) fortemente blindadas por `decorators` de permissão.

---

<div align="center">
  <p>Desenvolvido com 🩵 e muito <strong>Azul Bebê</strong></p>
</div>
