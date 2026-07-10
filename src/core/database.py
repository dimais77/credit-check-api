from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.config import get_settings

db_config = get_settings().db

engine = create_async_engine(
    str(db_config.url),
    echo=db_config.echo,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_pre_ping=True,
    connect_args={
        "server_settings": {
            "statement_timeout": str(db_config.statement_timeout_ms),
            "lock_timeout": str(db_config.lock_timeout_ms),
        },
    },
)
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as session:
        yield session


async def dispose() -> None:
    await engine.dispose()
