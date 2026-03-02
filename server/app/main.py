"""
CyberSentinel DLP - Main FastAPI Application
Enterprise-grade Data Loss Prevention Platform
"""

import logging
import sys
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_databases, close_databases, Base
import app.core.database as _db
from app.core.cache import init_cache, close_cache
from app.core.opensearch import init_opensearch, close_opensearch
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.api.v1 import api_router

# Setup structured logging
setup_logging()
logger = structlog.get_logger()


async def _auto_init_schema_and_admin():
    """Create tables if missing and seed the default admin user on first boot."""
    from sqlalchemy import text
    from app.core.security import get_password_hash

    # Import all models so Base.metadata knows about them
    import app.models.user  # noqa: F401
    import app.models.agent  # noqa: F401
    import app.models.policy  # noqa: F401
    import app.models.event  # noqa: F401
    import app.models.alert  # noqa: F401
    import app.models.google_drive  # noqa: F401
    import app.models.onedrive  # noqa: F401
    import app.models.classified_file  # noqa: F401

    # Check if tables already exist (avoid re-creating ENUM types which crashes asyncpg)
    async with _db.postgres_engine.connect() as conn:
        result = await conn.execute(
            text("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='users')")
        )
        tables_exist = result.scalar()

    if not tables_exist:
        async with _db.postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")
    else:
        logger.info("Database tables already exist, skipping creation")

    # Seed default admin if no users exist yet
    async with _db.postgres_session_factory() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM users")
        )
        user_count = result.scalar()
        if user_count == 0:
            hashed = get_password_hash("admin")
            await session.execute(
                text(
                    "INSERT INTO users (id, email, hashed_password, full_name, role, organization, is_active, is_verified, created_at, updated_at) "
                    "VALUES (gen_random_uuid(), 'admin', :pw, 'Administrator', 'ADMIN', 'CyberSentinel', TRUE, TRUE, NOW(), NOW())"
                ),
                {"pw": hashed},
            )
            await session.commit()
            logger.info("Default admin user created (username: admin, password: admin)")
        else:
            logger.info("Users table already populated, skipping admin seed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting CyberSentinel DLP Server", version=settings.VERSION)

    try:
        # Initialize databases
        await init_databases()
        logger.info("Databases initialized successfully")

        # Auto-create tables and seed default admin user on first boot
        await _auto_init_schema_and_admin()

        # Initialize cache
        await init_cache()
        logger.info("Cache initialized successfully")

        # Initialize OpenSearch
        await init_opensearch()
        logger.info("OpenSearch initialized successfully")

        # Additional startup tasks
        logger.info("Server startup complete",
                   environment=settings.ENVIRONMENT,
                   debug=settings.DEBUG,
                   port=settings.PORT)

        yield

    finally:
        # Shutdown
        logger.info("Shutting down CyberSentinel DLP Server")

        await close_opensearch()
        await close_cache()
        await close_databases()

        logger.info("Server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version=settings.VERSION,
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)


# Middleware Configuration
# ========================

# Request ID tracking
app.add_middleware(RequestIDMiddleware)

# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window_seconds=settings.RATE_LIMIT_WINDOW,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# Exception Handlers
# ==================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions
    """
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please contact support.",
            "request_id": request.state.request_id if hasattr(request.state, 'request_id') else None,
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handler for validation errors
    """
    logger.warning(
        "Validation error",
        error=str(exc),
        path=request.url.path,
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "message": str(exc),
        },
    )


# API Routes
# ==========

@app.get("/", tags=["Root"])
async def root() -> dict:
    """
    Root endpoint - Health check
    """
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint for load balancers and monitoring
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check() -> dict:
    """
    Readiness check endpoint for Kubernetes
    """
    from app.core.database import postgres_engine, mongodb_client
    from app.core.cache import redis_client
    from app.core.opensearch import opensearch_client
    from sqlalchemy import text

    services_status = {
        "database": "disconnected",
        "cache": "disconnected",
        "search": "unavailable"
    }

    try:
        # Check PostgreSQL connection
        if postgres_engine:
            async with postgres_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            services_status["database"] = "connected"

        # Check MongoDB connection
        if mongodb_client:
            await mongodb_client.admin.command("ping")

        # Check Redis connection
        if redis_client:
            await redis_client.ping()
            services_status["cache"] = "connected"

        # Check OpenSearch connection (optional - not required for readiness)
        if opensearch_client:
            try:
                await opensearch_client.info()
                services_status["search"] = "connected"
            except Exception:
                services_status["search"] = "unavailable"
                logger.warning("OpenSearch unavailable during readiness check")

        # Server is ready if database and cache are connected
        # OpenSearch is optional
        is_ready = (services_status["database"] == "connected" and
                   services_status["cache"] == "connected")

        if not is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "unready",
                    "services": services_status,
                },
            )

        return {
            "status": "ready",
            **services_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unready",
                "error": str(e),
                "services": services_status
            },
        )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True,
    )
