"""Async SQLAlchemy database engine and session."""

import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./truthlens.db")

# ponytail: SQLite doesn't support real pooling — these kwargs are no-ops
# but if DATABASE_URL is switched to PostgreSQL, pool_size and max_overflow kick in
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5 if "sqlite" not in DATABASE_URL else 1,
    max_overflow=10 if "sqlite" not in DATABASE_URL else 0,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    """FastAPI dependency — yields a DB session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
