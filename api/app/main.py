from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from .ai_schemas import CompareRequest, CompareResponse
from .orchestrator import compare
from .security import require_api_key
from .settings import settings


engine = create_async_engine(settings.database_url, pool_pre_ping=True)
redis_client = Redis.from_url(settings.redis_url, decode_responses=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title="UNX2 Core API",
    version="0.3.0",
    description="LÉVIATHAN secure gateway for three real model providers.",
    lifespan=lifespan,
)


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


@app.post(
    "/api/v1/ai/compare",
    response_model=CompareResponse,
    tags=["ai"],
    summary="Query GPT, Claude and Gemini, then run a Meta-Arbiter pass",
)
async def compare_three_intelligences(
    request: CompareRequest,
    _: str = Depends(require_api_key),
) -> CompareResponse:
    return await compare(request)


@app.get("/api/v1/modules", tags=["modules"])
async def modules() -> dict[str, Any]:
    return {
        "platform": "UNX2",
        "modules": [
            {"id": "leviathan-core", "name": "LÉVIATHAN CORE", "status": "three-provider-foundation"}
        ],
        "note": "Tenant identity, per-user authorization, durable audit storage, and production rate limits are not yet implemented. Do not expose this API publicly before those gates are complete.",
    }
