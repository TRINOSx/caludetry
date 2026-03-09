import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    alerts,
    billing,
    health,
    insights,
    parcelas,
    predictions,
    sensors,
    tenants,
)

settings = get_settings()

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("VOC Mesh Platform API starting up...")

    # Initialize Redis connection pool
    try:
        app.state.redis = redis.from_url(
            settings.REDIS_URL, decode_responses=True
        )
        await app.state.redis.ping()
        logger.info("Redis connection established")
    except Exception as exc:
        logger.warning("Redis unavailable, caching disabled: %s", exc)
        app.state.redis = None

    # Database engine is already initialized via module-level import in database.py
    logger.info("Database engine ready")

    yield

    # Shutdown
    if app.state.redis:
        await app.state.redis.aclose()
        logger.info("Redis connection closed")

    from app.database import engine

    await engine.dispose()
    logger.info("Database engine disposed")


app = FastAPI(
    title="VOC Mesh Platform API",
    version="1.0.0",
    description="Multi-Tenant AgriTech SaaS platform for VOC sensor mesh networks",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health.router)
app.include_router(tenants.router)
app.include_router(sensors.router)
app.include_router(parcelas.router)
app.include_router(predictions.router)
app.include_router(alerts.router)
app.include_router(insights.router)
app.include_router(billing.router)
