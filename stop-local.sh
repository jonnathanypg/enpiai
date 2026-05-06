#!/bin/bash

# EnpiAI - Stop All Local Services
echo "🛑 Stopping all EnpiAI services..."

# Kill processes on known ports
for PORT in 3000 3001 5000; do
    PID=$(lsof -ti :$PORT 2>/dev/null)
    if [ -n "$PID" ]; then
        echo "Killing process on port $PORT (PID: $PID)"
        kill -9 $PID 2>/dev/null
    fi
done

# Kill Celery workers
pkill -f "celery -A celery_app" 2>/dev/null && echo "Celery workers stopped."

# Kill Redis (only the one we started)
pkill -f "redis-server" 2>/dev/null && echo "Redis stopped."

# Clean Next.js lock file
rm -f frontend/.next/dev/lock 2>/dev/null

echo "✅ All services stopped."
