from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.ai.schemas import ParsedItem


class BasketRequest(BaseModel):
    text: str = Field(min_length=2, max_length=2000, description="The grocery list, free text")
    store_ids: list[UUID] | None = Field(None, description="One branch per chain (default: all tracked branches)")


class PickIn(BaseModel):
    store_id: UUID
    index: int = Field(ge=0)
    item_code: str = Field(min_length=1, max_length=20)
    confidence: Literal["high", "low", "remembered"]
    reason: str = Field(max_length=300)


class RepriceRequest(BaseModel):
    items: list[ParsedItem] = Field(min_length=1, max_length=60)
    store_ids: list[UUID] = Field(min_length=1, max_length=10)
    picks: list[PickIn] = Field(max_length=600)


class Alternative(BaseModel):
    item_code: str
    name: str
    price: Decimal


class BasketLine(BaseModel):
    index: int
    match_key: str = Field(description="Send back with PUT /api/matches to confirm or swap this product")
    item_code: str | None
    name: str | None
    is_weighted: bool | None
    regular_price: Decimal | None
    line_total: Decimal | None
    estimated_kg: Decimal | None = Field(None, description="Set when a counted item is sold by weight: the kilos priced")
    deal: str | None
    confidence: Literal["high", "low", "remembered"] | None
    reason: str | None
    alternatives: list[Alternative] = Field(description="Other products the search found, for swapping")


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
    remembered_matches: int = Field(description="Product picks taken from your saved choices")
    ai_matches: int = Field(description="Product picks made by the AI this time")
