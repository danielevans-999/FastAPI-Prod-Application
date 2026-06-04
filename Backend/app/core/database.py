from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from .config import settings

# ── PostgreSQL ────────────────────────────────────────────

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,           # connections in pool
    max_overflow=20,        # extra connections allowed
    pool_pre_ping=True,     # test connections before use
    pool_recycle=3600,      # recycle connections every hour
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields db session per request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Redis ─────────────────────────────────────────────────

# redis_client = redis.from_url(
#     settings.REDIS_URL,
#     decode_responses=True,   # return strings not bytes
#     socket_connect_timeout=5,
#     socket_timeout=5,
# )


# def get_redis():
#     """FastAPI dependency — yields redis client"""
#     try:
#         yield redis_client
#     finally:
#         pass  # redis_client is shared — do not close
