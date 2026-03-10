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

# 3. WhatsApp Gateway (No build needed for npx mode)
echo "📱 Preparing WhatsApp Gateway..."
cd whatsapp-gateway
# Just ensure .env exists or other setup if needed
cd ..

# 4. Reload Processes
echo "🔄 Reloading PM2..."
pm2 reload ecosystem.config.js || pm2 start ecosystem.config.js

echo "✅ EnpiAI Deployment Complete!"
