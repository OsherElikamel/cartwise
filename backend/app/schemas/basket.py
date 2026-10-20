from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai.schemas import ParsedItem


class BasketRequest(BaseModel):
    text: str = Field(min_length=2, max_length=2000, description="The grocery list, free text")
    store_ids: list[UUID] | None = Field(None, description="One branch per chain (default: all tracked branches)")


class BasketLine(BaseModel):
    index: int
    item_code: str | None
    name: str | None
    is_weighted: bool | None
    regular_price: Decimal | None
    line_total: Decimal | None
    deal: str | None
    confidence: Literal["high", "low"] | None
    reason: str | None


class StoreBasket(BaseModel):
    store_id: UUID
    chain_slug: str
    chain_name: str
    store_name: str
    shared_total: Decimal
    full_total: Decimal
    missing: list[int]
    lines: list[BasketLine]


class BasketComparison(BaseModel):
    items: list[ParsedItem]
    shared_items: list[int] = Field(description="Indexes of items every branch has; the ranking uses only these")
    stores: list[StoreBasket] = Field(description="Cheapest first, by shared_total")
    savings_vs_most_expensive: Decimal
