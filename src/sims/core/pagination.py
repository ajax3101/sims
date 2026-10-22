from typing import Annotated

from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class PageParams(BaseModel):
    page: int = 1
    size: int = 25

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


def _page_params(page: int = Query(1, ge=1), size: int = Query(25, ge=1, le=200)) -> PageParams:
    return PageParams(page=page, size=size)


Paging = Annotated[PageParams, Depends(_page_params)]


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int


async def count(session: AsyncSession, stmt: Select) -> int:
    """Total rows of a filtered select (ordering and paging stripped)."""
    inner = stmt.order_by(None).limit(None).offset(None).subquery()
    return (await session.execute(select(func.count()).select_from(inner))).scalar_one()
