import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from sims.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
TEST_URL = get_settings().test_database_url


def alembic_config() -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", TEST_URL)
    return cfg


async def alembic(cmd: str, revision: str) -> None:
    # env.py calls asyncio.run(); run it off the test loop.
    await asyncio.to_thread(getattr(command, cmd), alembic_config(), revision)


@pytest.fixture(scope="session")
async def engine():
    await alembic("downgrade", "base")
    await alembic("upgrade", "head")
    eng = create_async_engine(TEST_URL, poolclass=NullPool)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine):
    """Session inside an outer transaction rolled back after the test.

    commit()/rollback() in the test act on a SAVEPOINT, so constraint
    violations can be asserted and the seeded reference data survives.
    """
    async with engine.connect() as conn:
        outer = await conn.begin()
        s = AsyncSession(bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint")
        try:
            yield s
        finally:
            await s.close()
            await outer.rollback()


@pytest.fixture
async def client(session):
    """API client whose requests share the test's rolled-back session."""
    from httpx import ASGITransport, AsyncClient

    from sims.core.db import get_session
    from sims.main import create_app

    app = create_app()

    async def _override():
        yield session

    app.dependency_overrides[get_session] = _override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
