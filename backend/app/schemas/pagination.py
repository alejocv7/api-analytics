from collections.abc import Sequence
from typing import Annotated, Any

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, computed_field


class PaginatedResult[T](BaseModel):
    """
    Internal bucket for service results that include a count.
    Used to pass items and total from service to route.
    """

    items: list[T] | Sequence[T]
    total: int
    pagination: PaginationParams


class PaginatedResponse[T](BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[T] | Sequence[T]
    total: int = Field(..., description="Total number of items available")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")

    @computed_field(description="Whether there is a next page")  # type: ignore[prop-decorator]
    @property
    def has_next(self) -> bool:
        return self.page * self.page_size < self.total

    @computed_field(description="Whether there is a previous page")  # type: ignore[prop-decorator]
    @property
    def has_previous(self) -> bool:
        return self.page > 1

    @classmethod
    def from_result(cls, result: PaginatedResult[Any]) -> PaginatedResponse[T]:
        return cls(
            items=result.items,
            total=result.total,
            page=result.pagination.page,
            page_size=result.pagination.page_size,
        )


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


PaginationQuery = Annotated[PaginationParams, Depends()]
