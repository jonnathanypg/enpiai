# EnpiAI Backend

## 🛠 Prerequisites
- Python 3.14+
- Redis (for Celery/Background Tasks)
- MySQL (Remote or Local)

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
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_secret_key
# ... other keys
```

### 3. Running Services

**Terminal 1: Flask API**
```bash
source venv/bin/activate
python3 app.py
```

**Terminal 2: Redis Server**
```bash
# MacOS (Homebrew)
brew services start redis
# OR manually
redis-server
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
