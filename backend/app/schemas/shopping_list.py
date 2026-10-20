from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.basket import BasketComparison


class ListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    text: str = Field(min_length=2, max_length=2000)


class ListUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    text: str | None = Field(None, min_length=2, max_length=2000)


class ListResponse(BaseModel):
    id: UUID
    name: str
    text: str
    is_parsed: bool
    updated_at: datetime


class ListCompareRequest(BaseModel):
    store_ids: list[UUID] | None = None


class RunSummary(BaseModel):
    id: UUID
    list_id: UUID | None
    list_name: str | None
    item_count: int
    cheapest_chain: str
    cheapest_total: Decimal
    savings: Decimal
    created_at: datetime


class RunDetail(RunSummary):
    result: BasketComparison
