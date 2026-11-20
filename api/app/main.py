from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from .skills import router as skills_router


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://unx2:unx2_dev_only@postgres:5432/unx2"
    redis_url: str = "redis://redis:6379/0"
    environment: str = "development"
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"


settings = Settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.redis = redis_client
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title="UNX2 Core API",
    version="0.2.0",
    description="UNX2 core API with additive LÉVIATHAN Skill Runtime. Existing MQTT broker remains a separate service.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(skills_router)


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok", "service": "unx2-api"}


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict[str, Any]:
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "unavailable"
    try:
        await redis_client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    if status != "ok":
        raise HTTPException(status_code=503, detail={"status": status, "checks": checks})
    return {"status": status, "checks": checks}


@app.get("/api/v1/modules", tags=["modules"])
async def modules() -> dict[str, Any]:
    return {
        "platform": "UNX2",
        "modules": [
            {"id": "emotion-factory", "name": "EMOTION FACTORY", "status": "foundation"},
            {"id": "leviathan-skill-runtime", "name": "LÉVIATHAN Skill Runtime", "status": "planning_only"},
        ],
        "note": "Skill routing is enabled; agent execution remains disabled until authentication, authorization, tenant isolation, audit logging, and migrations are implemented.",
    }
