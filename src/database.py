"""Database utilities and session management"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from src.models import Base
from src.config import DATABASE_URL
from src.logger import setup_logger

logger = setup_logger(__name__)

# Convert postgres:// to postgresql:// for SQLAlchemy 2.0 and handle asyncpg
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    database_url = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
elif DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
     database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    database_url = DATABASE_URL

# Create async engine
engine: AsyncEngine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database sessions.
    Handles commit/rollback automatically.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
