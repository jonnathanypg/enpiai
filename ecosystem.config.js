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
            name: "enpiai-backend",
            cwd: "./backend",
            // Absolute path for production (Linux), relative for local/mac
            interpreter: process.platform === 'linux' ? "/root/enpiai/backend/venv/bin/python" : require('path').join(__dirname, 'backend', 'venv', 'bin', 'python'),
            script: "app.py",
            env: {
                FLASK_ENV: "production",
                PORT: 5000,
                CELERY_BROKER_URL: "redis://localhost:6381/0",
                CELERY_RESULT_BACKEND: "redis://localhost:6381/1"
            }
        },
        {
            name: "enpiai-worker",
            cwd: "./backend",
            interpreter: process.platform === 'linux' ? "/root/enpiai/backend/venv/bin/python" : require('path').join(__dirname, 'backend', 'venv', 'bin', 'python'),
            script: "venv/bin/celery",
            args: "-A celery_app.celery worker --loglevel=info",
            env: {
                FLASK_ENV: "production",
                CELERY_BROKER_URL: "redis://localhost:6381/0",
                CELERY_RESULT_BACKEND: "redis://localhost:6381/1"
            }
        },
        {
            name: "enpiai-whatsapp",
            cwd: "./api-whatsapp",
            script: "./dist/app.js",
            env: {
                PORT: 3001,
                NODE_ENV: "production"
            }
        }
    ]
};
