module.exports = {
    apps: [
        {
            name: "enpiai-redis",
            script: "redis-server",
            args: "--port 6381 --bind 127.0.0.1 --requirepass YOUR_REDIS_PASS",
            env: {
                NODE_ENV: "production"
            }
        },
        {
            name: "enpiai-frontend",
            cwd: "./frontend",
            script: "npm",
            args: "start",
            env: {
                NODE_ENV: "production",
                PORT: 3000
            }
        },
        {
            name: "enpiai-fastapi",
            cwd: "./backend",
            script: "/root/enpiai/backend/venv/bin/uvicorn",
            args: "fastapi_app:app --host 127.0.0.1 --port 5000 --workers 2",
            interpreter: "none",
            env: {
                FLASK_ENV: "production",
                DATABASE_URL: process.env.DATABASE_URL
            }
        },
        {
            name: "enpiai-worker",
            cwd: "./backend",
            interpreter: "/root/enpiai/backend/venv/bin/python",
            script: "venv/bin/celery",
            args: "-A celery_app.celery worker --loglevel=info --concurrency=2",
            env: {
                FLASK_ENV: "production",
                CELERY_BROKER_URL: "redis://:YOUR_REDIS_PASS@127.0.0.1:6381/0",
                CELERY_RESULT_BACKEND: "redis://:YOUR_REDIS_PASS@127.0.0.1:6381/1"
            }
        },
        {
            name: "enpiai-cron",
            cwd: "./backend",
            interpreter: "/root/enpiai/backend/venv/bin/python",
            script: "run_cron.py",
            env: {
                FLASK_ENV: "production"
            }
        },
        {
            name: "enpiai-whatsapp",
            cwd: "./api-whatsapp",
            script: "./dist/app.js",
            max_memory_restart: "500M",
            env: {
                PORT: 3001,
                NODE_ENV: "production",
                BACKEND_URL: "http://localhost:5000",
                API_SECRET: process.env.WHATSAPP_API_SECRET
            }
        }
    ]
};
