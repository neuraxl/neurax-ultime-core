"""Shared SQLAlchemy engine for UNX2 API modules."""
import os
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://unx2:unx2_dev_only@postgres:5432/unx2",
)
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
