from typing import Annotated

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, computed_field


class PaginatedResponse[T](BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[T]
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


class PaginationParams(BaseModel):
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


PaginationQuery = Annotated[PaginationParams, Depends()]
