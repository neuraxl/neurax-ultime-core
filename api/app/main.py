from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from redis.asyncio import Redis
from sqlalchemy import text

from .auth import router as auth_router
from .crm import router as crm_router
from .db import engine
from .main_config import settings
from .models import Base


redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # MVP bootstrap. Replace with versioned Alembic migrations before production.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title="UNX2 Core API",
    version="0.2.0",
    description="UNX2 shared API with tenant-scoped EMOTION FACTORY CRM. MQTT remains independent.",
    lifespan=lifespan,
)
app.include_router(auth_router)
app.include_router(crm_router)


@app.get("/", include_in_schema=False)
async def emotion_factory_workspace():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


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
        "modules": [{"id": "emotion-factory", "name": "EMOTION FACTORY",
                     "status": "crm-mvp", "tenant_isolated": True}],
    }
