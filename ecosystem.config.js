module.exports = {
    apps: [
        {
            name: "enpiai-redis",
            script: "redis-server",
            args: "--port 6379",
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
                PORT: 5000
            }
        },
        {
            name: "enpiai-worker",
            cwd: "./backend",
            interpreter: process.platform === 'linux' ? "/root/enpiai/backend/venv/bin/python" : require('path').join(__dirname, 'backend', 'venv', 'bin', 'python'),
            script: "venv/bin/celery",
            args: "-A celery_app.celery worker --loglevel=info",
            env: {
                FLASK_ENV: "production"
            }
        },
        {
            name: "enpiai-whatsapp",
            cwd: "./whatsapp-gateway",
            script: "npx",
            args: "-y @agenticnucleus/whatsapp-multitenant",
            env: {
                PORT: 3001
            }
        }
    ]
};
