# src/database/postgres.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.security.config import settings
from .models import Base

# Асинхронный engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    future=True
)

# Фабрика сессий
AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

async def get_db() -> AsyncSession:
    """
    Dependency для получения асинхронной сессии БД
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_tables():
    """
    Создание всех таблиц (для разработки)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Все таблицы созданы")

async def delete_tables():
    """
    Удаление всех таблиц (только для тестов!)
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("🗑️ Все таблицы удалены")