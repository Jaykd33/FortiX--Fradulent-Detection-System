# app/core/db.py
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from app.core.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _is_sqlite(url: str) -> bool:
    # works for "sqlite:///" and "sqlite+aiosqlite:///"
    return url.startswith("sqlite")


# --- Engine ---
if _is_sqlite(settings.DATABASE_URL):
    # Ensure you're using the async driver for SQLite
    # e.g. settings.DATABASE_URL = "sqlite+aiosqlite:///./app.db"
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        future=True,
        connect_args={"timeout": 30},  # busy timeout at driver-level
    )

    # Apply SQLite PRAGMAs to reduce "database is locked" issues
    @event.listens_for(async_engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Write-Ahead Logging allows one writer + many readers
        cursor.execute("PRAGMA journal_mode=WAL;")
        # Good durability/perf tradeoff for apps
        cursor.execute("PRAGMA synchronous=NORMAL;")
        # Extra busy timeout at SQL level (ms)
        cursor.execute("PRAGMA busy_timeout=5000;")
        cursor.close()
else:
    # Postgres/MySQL etc.
    async_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_pre_ping=True,
        future=True,
    )


# --- Session factory ---
async_session_factory = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


# --- Dependency ---
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = async_session_factory()
    try:
        yield session
    finally:
        await session.close()
