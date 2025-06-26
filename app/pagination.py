from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, computed_field
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from .config import settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(
        settings.default_page_size,
        ge=1,
        le=settings.max_page_size,
        description="Items per page",
    )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.limit


class PaginatedResult(BaseModel, Generic[T]):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    limit: int = Field(ge=1)

    @computed_field
    def pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit

    @computed_field
    def has_next(self) -> bool:
        return self.page < self.pages

    @computed_field
    def has_prev(self) -> bool:
        return self.page > 1


def paginate_select(
    db: Session, stmt: Select, pagination: PaginationParams
) -> tuple[list[Any], int]:
    """
    Paginate a SQLAlchemy Select statement (v2 API).

    Args:
        db: Database session
        stmt: SQLAlchemy Select statement to paginate
        pagination: Pagination parameters

    Returns:
        Tuple of (items list, total_count)
    """
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar()

    # Get paginated items
    items_stmt = stmt.offset(pagination.offset).limit(pagination.limit)
    items = db.execute(items_stmt).scalars().unique().all()

    return items, total


def create_paginated_result(
    items: list[T], total: int, pagination: PaginationParams
) -> PaginatedResult[T]:
    """
    Create a PaginatedResult from items and pagination info.

    Args:
        items: List of items for current page
        total: Total count of items
        pagination: Pagination parameters

    Returns:
        PaginatedResult with items and metadata
    """
    return PaginatedResult(
        items=items,
        total=total,
        page=pagination.page,
        limit=pagination.limit,
    )
