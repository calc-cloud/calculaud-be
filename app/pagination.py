from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy.orm import Query

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

    @property
    def pages(self) -> int:
        return (self.total + self.limit - 1) // self.limit

    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


def paginate(
    query: Query, pagination: PaginationParams
) -> tuple[list[Any], int]:
    """
    Paginate a SQLAlchemy query.

    Args:
        query: SQLAlchemy query to paginate
        pagination: Pagination parameters

    Returns:
        Tuple of (items list, total_count)
    """
    total = query.count()

    items = query.offset(pagination.offset).limit(pagination.limit).all()

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
