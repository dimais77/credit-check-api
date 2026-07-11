from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.config import get_settings
from core.database import get_session
from main import app
from models import Base


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    test_url = get_settings().db.test_url
    if test_url is None:
        raise RuntimeError("APP_CONFIG__DB__TEST_URL must be set to run the test suite")
    engine = create_async_engine(str(test_url), poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as connection:
        await connection.begin()
        factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        async with factory() as s:
            yield s
        await connection.rollback()


@pytest.fixture
async def client(session: AsyncSession, tmp_path: Path) -> AsyncIterator[AsyncClient]:
    async def get_session_override() -> AsyncIterator[AsyncSession]:
        yield session

    test_settings = get_settings().model_copy(deep=True)
    test_settings.storage.dir = tmp_path

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_settings] = lambda: test_settings
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
