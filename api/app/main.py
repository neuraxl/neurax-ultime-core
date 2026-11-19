from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text
from .config import settings
from .database import engine
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()
    await redis_client.aclose()

app = FastAPI(title="UNX2 Core API", version="0.3.0",
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
        "note": "Tenant identity, API-key hashing, RBAC primitives, audit events, and Alembic migrations are available; registry data-plane tenant isolation remains a required next step before commercial activation."}

from .open_source_registry import router as open_source_registry_router
app.include_router(open_source_registry_router)

from .security import router as security_router
app.include_router(security_router)
