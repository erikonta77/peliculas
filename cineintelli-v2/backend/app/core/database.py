"""
Configuración de base de datos SQLAlchemy async
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Base declarativa para modelos
Base = declarative_base()

# Crear engine async
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    echo=settings.DEBUG,
)

# Session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    """Dependency para obtener sesión de base de datos."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Inicializa la base de datos creando tablas."""
    async with engine.begin() as conn:
        # Importar modelos para que se registren
        from app.models import movie, user
        await conn.run_sync(Base.metadata.create_all)
