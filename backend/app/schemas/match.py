from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MatchChoice(BaseModel):
    match_key: str = Field(min_length=1, max_length=200, description="From the basket line")
    store_id: UUID = Field(description="The branch the choice was made at")
    item_code: str = Field(min_length=1, max_length=20)


class MatchResponse(BaseModel):
    id: UUID
    match_key: str
    chain_slug: str
    chain_name: str
    item_code: str
    item_name: str
    updated_at: datetime
