# FastAPI Production Backend

## Project Structure

```
fastapi_production/
├── app/
│   ├── __init__.py
│   ├── main.py                  ← FastAPI app, middleware, routers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            ← All settings from .env
│   │   ├── security.py          ← JWT, password hashing
│   │   ├── database.py          ← SQLAlchemy + Redis connections
│   │   └── dependencies.py      ← Shared FastAPI dependencies
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py            ← All SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── schemas.py           ← All Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py              ← Register, login, refresh, logout
│   │   ├── users.py             ← User CRUD + profile
│   │   ├── files.py             ← Upload/download
│   │   ├── payments.py          ← Payment gateway integration
│   │   ├── notifications.py     ← Email + SMS
│   │   ├── websockets.py        ← Real time features
│   │   ├── admin.py             ← Admin dashboard (role protected)
│   │   └── ai.py                ← OpenAI powered endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py     ← Email sending logic
│   │   ├── sms_service.py       ← SMS sending logic
│   │   ├── payment_service.py   ← Payment processing logic
│   │   ├── cache_service.py     ← Redis caching logic
│   │   ├── file_service.py      ← File handling logic
│   │   └── ai_service.py        ← OpenAI integration
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── celery_tasks.py      ← All Celery background tasks
│   └── middleware/
│       ├── __init__.py
│       └── middleware.py        ← Logging, timing, security headers
├── tests/
│   └── test_auth.py
├── scripts/
│   └── create_admin.py          ← Script to create first admin user
├── .env.example
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
└── nginx.conf
```

## Quick Start

```bash
# 1. Clone and setup
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Start Redis (required for caching + Celery)
docker run -d -p 6379:6379 redis:alpine

# 5. Run the server
uvicorn app.main:app --reload

# 6. Start Celery worker (separate terminal)
celery -A app.tasks.celery_tasks worker --loglevel=info

# 7. Visit docs
http://127.0.0.1:8000/docs
```
