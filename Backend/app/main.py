from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from loguru import logger

from .core.config import settings
from .core.database import engine, Base
from .middleware.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware


# ── Routers ───────────────────────────────────────────────
from .routers import auth, users, files, payments, notifications, websockets, admin, ai

# ── Create all DB tables ──────────────────────────────────
Base.metadata.create_all(bind=engine)

# ── Rate Limiter ──────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.RATE_LIMIT_PER_MINUTE}/minute"]
)

# ── FastAPI App ───────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Highly Available FastAPI Backend

### Features
- JWT Authentication (register, login, refresh, logout)
- Role Based Access Control (admin, staff, user)
- File Upload & Download
- Payment Gateway Integration (Flutterwave)
- Real Time WebSockets (chat + notifications)
- Background Tasks (email + SMS via Celery)
- Redis Caching + Rate Limiting
- AI Powered Endpoints (OpenAI)
- Admin Dashboard

### Authentication
Use the `/api/auth/login` endpoint to get a JWT token,
then click **Authorize** and enter: `Bearer your-token-here`
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── Rate Limiting ─────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ──────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React dev server
        "http://localhost:8080",    # Vue dev server
        "https://yourdomain.com",   # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Custom Middleware ─────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# ── Routers ───────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(files.router)
app.include_router(payments.router)
app.include_router(notifications.router)
app.include_router(websockets.router)
app.include_router(admin.router)
app.include_router(ai.router)


# ── Lifecycle Events ──────────────────────────────────────
@app.on_event("startup")
async def startup():
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Docs: http://127.0.0.1:8000/docs")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Server shutting down...")


# ── Health Check ──────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app":         settings.APP_NAME,
        "version":     settings.APP_VERSION,
        "status":      "running",
        "environment": settings.ENVIRONMENT,
        "docs":        "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for load balancers"""
    from app.core.database import redis_client
    try:
        redis_client.ping()
        redis_ok = True
    except:
        redis_ok = False

    return {
        "status":    "healthy",
        "database":  "connected",
        "redis":     "connected" if redis_ok else "disconnected",
    }


# ── Global Exception Handler ──────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc) if settings.DEBUG else "Contact support"}
    )
