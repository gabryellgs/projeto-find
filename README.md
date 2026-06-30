# FIND Platform

**Find** is a comprehensive, centralized ecosystem for lost and found asset management, designed for institutional environments. It bridges web, mobile, and IoT interfaces to deliver real-time item tracking and seamless communication between users.

---

## 🏗️ Architecture & Ecosystem

The platform is structured into three integrated components:

1. **Web Dashboard (SaaS)**: A responsive, high-fidelity administrative panel built with Django. It features a modern Glassmorphism UI, ensuring a premium user experience. Includes permission-based routing for administrators and scholarship holders.
2. **Mobile Application**: A React Native cross-platform application ensuring native mobile experiences with fluid gestures and intuitive UI design.
3. **IoT Integration**: Hardware-level integration utilizing ESP32 microcontrollers and RFID technology for real-time asset validation and scanning.

---

## 🛠️ Technology Stack

**Backend Infrastructure**
- **Framework**: Django 5.0 (Python 3.12)
- **Database**: PostgreSQL (Production) / SQLite (Development)
- **Authentication**: Native session management and Google OAuth2 integration.
- **Server**: Gunicorn (WSGI HTTP Server)

**Frontend (Web)**
- HTML5, CSS3, JavaScript (ES6+)
- Custom UI framework using Bootstrap 5 architecture.
- Interactive map components via Leaflet.js.
- Image hashing and processing tools via Pillow and python-magic.

**DevOps & Deployment**
- Containerization: Docker & Docker Compose
- Continuous Deployment Pipeline via Render Platform.

---

## ⚙️ Prerequisites

Before you begin, ensure you have met the following requirements:
- Python 3.12+
- Docker and Docker Compose (For containerized deployment)
- Git (Version control)
- System dependencies (Linux/Ubuntu): `libmagic1`, `default-libmysqlclient-dev`

---

## 🚀 Installation & Setup

### Option A: Containerized Environment (Recommended)
This approach automatically provisions the database, applies migrations, and gathers static assets.

1. Clone the repository:
   ```bash
   git clone https://github.com/gabryellgs/projeto-find.git
   cd projeto-find
   ```
2. Build and initialize the Docker containers:
   ```bash
   docker-compose build web
   docker-compose up -d web
   ```
3. Access the application at `http://localhost:8000`.

### Option B: Local Development Environment

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute database migrations and seed default data:
   ```bash
   python manage.py migrate
   python manage.py criar_categorias
   python manage.py gerar_hashes
   ```
4. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```
5. Initialize the development server:
   ```bash
   python manage.py runserver
   ```

---

## ☁️ Deployment Guide

The application is configured for seamless deployment to PaaS providers (e.g., Render, Heroku). 

1. Connect the GitHub repository to your Render Web Service.
2. Select the **Docker** runtime environment.
3. The embedded `Dockerfile` and `start.sh` scripts will automatically manage static file compilation (`collectstatic`), WSGI configuration, and database migrations.

---

## 🔐 Security & Compliance

- **LGPD/GDPR Compliance**: Includes built-in consent management logic for cookie tracking and privacy policies.
- **Access Control**: Role-Based Access Control (RBAC) separating administrative actions from standard user permissions.
- **Data Protection**: Enforced CSRF tokens, secure cookie flags, and parameterized query execution to prevent injection attacks.

---

*Find Platform - Proprietary License. All rights reserved.*
