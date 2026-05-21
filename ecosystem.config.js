module.exports = {
    apps: [
        {
            name: "enpiai-redis",
            script: "redis-server",
            args: "--port 6381",
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
            args: "fastapi_app:app --host 0.0.0.0 --port 5000 --workers 2",
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
                CELERY_BROKER_URL: "redis://localhost:6381/0",
                CELERY_RESULT_BACKEND: "redis://localhost:6381/1",
                C_FORCE_ROOT: "true"
            }
        },
        {
            name: "enpiai-cron",
            cwd: "./backend",
            interpreter: "/root/enpiai/backend/venv/bin/python",
            script: "run_cron.py",
            env: {
                FLASK_ENV: "production",
                C_FORCE_ROOT: "true"
            }
        },
        {
            name: "enpiai-api-whatsapp",
            cwd: "./api-whatsapp",
            script: "./dist/app.js",
            env: {
                PORT: 3001,
                NODE_ENV: "production"
            }
        }
    ]
};
