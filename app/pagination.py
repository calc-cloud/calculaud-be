from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Query, Session

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
    db: Session, query: Query, pagination: PaginationParams
) -> tuple[list, int]:
    """
    Paginate a SQLAlchemy query.

    Args:
        db: Database session
        query: SQLAlchemy query to paginate
        pagination: Pagination parameters

    Returns:
        Tuple of (items, total_count)
    """
    total = db.scalar(query.statement.with_only_columns(func.count()).order_by(None))

    items = query.offset(pagination.offset).limit(pagination.limit).all()

    return items, total or 0
