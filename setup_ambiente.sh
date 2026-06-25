#!/usr/bin/env bash
# Script para configurar o ambiente do Find em um novo PC

echo "📦 Instalando dependências do requirements.txt..."
pip install -r requirements.txt

echo "⚙️ Configurando o arquivo .env para desenvolvimento..."
# Cria o .env apenas se ele não existir
if [ ! -f .env ]; then
    echo "DEBUG=True" > .env
    echo "ALLOWED_HOSTS=localhost,127.0.0.1,*" >> .env
    echo "Arquivo .env criado com sucesso para ambiente de desenvolvimento!"
else
    echo "Arquivo .env já existe, pulando criação."
fi

echo "🎨 Coletando arquivos estáticos (CSS/JS)..."
python manage.py collectstatic --noinput

echo "🗄️ Preparando e rodando as migrações do banco de dados (Models)..."
python manage.py makemigrations
python manage.py migrate

echo "✅ Ambiente configurado com sucesso!"
echo "🚀 Para iniciar o servidor, rode: python manage.py runserver 0.0.0.0:8000"
