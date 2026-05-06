#!/bin/bash
set -e

# 0. Ensure Env Vars
export PATH=$PATH:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -f ~/.bashrc ] && source ~/.bashrc

echo "🚀 Starting EnpiAI Deployment..."

# 1. Frontend
echo "⚛️ Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 2. Backend
echo "🐍 Updating Backend..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 3. WhatsApp Gateway (Standalone Mode A via local microservice)
echo "📱 Preparing WhatsApp Gateway (api-whatsapp)..."
cd api-whatsapp
if [ ! -f ".env" ]; then
    echo "⚠️ Warning: api-whatsapp/.env not found. Creating a template..."
    echo "MYSQL_HOST=localhost" > .env
    echo "MYSQL_USER=root" >> .env
    echo "MYSQL_PASSWORD=" >> .env
    echo "MYSQL_DATABASE=enpiai" >> .env
    echo "BACKEND_URL=http://localhost:5000" >> .env
    echo "PORT=3001" >> .env
    echo "❗️ IMPORTANT: Please edit api-whatsapp/.env with your real DB credentials before PM2 starts."
fi
echo "📦 Installing and Building WhatsApp Microservice..."
npm install
npm run build
cd ..

# 4. Reload Processes
echo "🔄 Reloading PM2..."
pm2 reload ecosystem.config.js || pm2 start ecosystem.config.js

echo "✅ EnpiAI Deployment Complete!"
