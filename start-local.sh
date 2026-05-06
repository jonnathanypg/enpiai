#!/bin/bash

# EnpiAI Local PM2 Startup Script
# This script prepares the environment and starts all services using PM2,
# giving you a "production-like" experience locally with a clean terminal.

echo "🚀 Starting EnpiAI local environment via PM2..."

# 1. Ensure Frontend is built for production
echo "⚛️ Building Frontend for production..."
cd frontend
npm install
npm run build
cd ..

# 2. Stop any manual background processes that might conflict
echo "🧹 Cleaning up old stray processes..."
for PORT in 3000 3001 5000; do
    PID=$(lsof -ti :$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        kill -9 $PID 2>/dev/null
    fi
done
pkill -f "celery -A celery_app" 2>/dev/null
pkill -f "redis-server" 2>/dev/null

# 3. Start everything with PM2 using the ecosystem file
echo "🔄 Launching cluster with PM2..."
pm2 restart ecosystem.config.js 2>/dev/null || pm2 start ecosystem.config.js

echo ""
echo "✅ All services successfully launched in the background!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:5000"
echo "  WhatsApp:  http://localhost:3001"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Para ver los logs en vivo, ejecuta:"
echo "     pm2 logs"
echo ""
echo "🛑 Para detener todo, ejecuta:"
echo "     pm2 stop all"
echo ""
