# app/database.py
import json
from typing import AsyncGenerator

from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings  # keep your settings with DATABASE_URL

# Async engine for asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

# Async session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def create_db_and_tables() -> None:
    """
    Create tables (sync create_all invoked via run_sync with an async conn).
    Also checks PostGIS presence.
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        try:
            result = await conn.execute(text("SELECT PostGIS_Full_Version()"))
            print("PostGIS Version Check:", result.scalar_one_or_none())
        except Exception as e:
            print("PostGIS not available or error:", e)


# Dependency for FastAPI endpoints (returns an AsyncSession)
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
