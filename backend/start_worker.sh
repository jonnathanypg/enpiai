#!/bin/bash
# Start Celery worker with all environment variables loaded from .env
set -a
source /root/enpiai/backend/.env
set +a

export PYTHONPATH=/root/enpiai/backend

exec /root/enpiai/backend/venv/bin/python -m celery \
    -A celery_app.celery worker \
    --loglevel=info \
    --concurrency=2
