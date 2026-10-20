from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class ChainResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    name_he: str
    store_count: int
    tracked_store_count: int


class StoreResponse(BaseModel):
    id: UUID
    chain_slug: str
    chain_name: str
    store_code: str
    name: str
    address: str | None
    is_tracked: bool
    is_ready: bool = False


class Deal(BaseModel):
    description: str
    min_qty: Decimal
    unit_price: Decimal


class ProductResult(BaseModel):
    store_id: UUID
    chain_slug: str
    chain_name: str
    item_code: str
    name: str
    manufacturer: str | None
    is_weighted: bool
    price: Decimal
    unit_price: Decimal | None
    deal: Deal | None
    score: float
