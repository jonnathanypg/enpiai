# EnpiAI Backend

## 🛠 Prerequisites
- Python 3.12+
- Redis 6.2+ (Port 6381 for EnpiAI)
- MySQL 8.0 (Remote or Local)

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Ensure your `.env` file is populated with:
```ini
DATABASE_URL=mysql+pymysql://user:pass@host/dbname
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
REDIS_URL=redis://localhost:6381/0
SECRET_KEY=your_secret_key
# ... other keys
```

### 3. Running Services

**Terminal 1: Unified Gateway (FastAPI)**
```bash
source venv/bin/activate
python3 fastapi_app.py
```

**Terminal 2: Redis Server**
```bash
# Ensure Redis is running on port 6381
redis-server --port 6381
```

**Terminal 3: Celery Worker**
```bash
source venv/bin/activate
celery -A celery_app.celery worker --loglevel=info
```

### 4. Database Seeding
To create the initial Super Admin and Test Distributor:
```bash
source venv/bin/activate
python3 seed_users.py
```
