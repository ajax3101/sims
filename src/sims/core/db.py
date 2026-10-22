from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from sims.core.config import get_settings
from sims.core.errors import Conflict

# Deterministic constraint names: Alembic can drop/alter what it created.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def create_engine(url: str | None = None) -> AsyncEngine:
    return create_async_engine(url or get_settings().database_url)


def make_sessionmaker(bind) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=bind, expire_on_commit=False)


_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = make_sessionmaker(create_engine())
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    async with get_sessionmaker()() as session:
        yield session


async def commit(session: AsyncSession) -> None:
    """Commit; a constraint violation becomes Conflict (409) with the constraint name."""
    try:
        await session.commit()
    except IntegrityError as exc:
        cause = getattr(exc.orig, "__cause__", None)
        constraint = getattr(cause, "constraint_name", None)  # read before rollback
        detail = str(getattr(cause, "detail", None) or getattr(cause, "message", None) or "constraint violated")
        await session.rollback()
        raise Conflict(detail, constraint) from exc
