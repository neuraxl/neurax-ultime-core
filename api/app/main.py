from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "postgresql+psycopg://unx2:unx2_dev_only@postgres:5432/unx2"
    redis_url: str = "redis://redis:6379/0"
    environment: str = "development"
    os_registry_admin_token: str | None = None

settings = Settings()
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

@asynccontextmanager
async def lifespan(_: FastAPI):
    from .open_source_registry import init_registry
    await init_registry()
    yield
    await engine.dispose()
    await redis_client.aclose()

app = FastAPI(title="UNX2 Core API", version="0.2.0",
    description="UNX2 Core API with an additive open-source discovery and connector registry. Existing MQTT broker remains independent.",
    lifespan=lifespan)

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
    return {"platform": "UNX2", "modules": [
        {"id": "emotion-factory", "name": "EMOTION FACTORY", "status": "foundation"},
        {"id": "open-source-registry", "name": "UNX2 Open Source Registry", "status": "foundation"}],
        "note": "CRM and commercial actions remain disabled until tenant authentication, authorization, audit logging, and migrations are implemented."}

from .open_source_registry import router as open_source_registry_router
app.include_router(open_source_registry_router)
