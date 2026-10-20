"""The contract between CartWise and any LLM provider.

Providers return these exact shapes (enforced through each provider's
structured-output feature), so the rest of the app never parses free text.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ParsedItem(BaseModel):
    original: str = Field(description="The user's own words for this item, copied verbatim")
    search_terms: list[str] = Field(
        min_length=1, max_length=3,
        description="1-3 short Hebrew phrases as shelf labels might write the product: the main one first, "
        "then singular/plural or common spelling variants, e.g. ['עגבניות', 'עגבניה']",
    )
    quantity: float = Field(gt=0, description="How many units, or how many kilos when unit is 'kg'")
    unit: Literal["unit", "kg"]
    unit_weight_kg: float | None = Field(
        None, gt=0, le=30,
        description="Only when unit is 'unit' and the item is usually sold by weight (whole watermelon, "
        "melon, pineapple, cabbage, apples by count): the typical weight of ONE unit in kg",
    )
    brand: str | None = Field(None, description="Brand only if the user named one, in Hebrew")
    size: str | None = Field(None, description="Package size only if the user gave one, e.g. '1 ליטר'")


class ParsedList(BaseModel):
    items: list[ParsedItem]


class Candidate(BaseModel):
    item_code: str
    name: str
    manufacturer: str | None
    is_weighted: bool
    price: float


class MatchRequestItem(BaseModel):
    index: int
    item: ParsedItem
    candidates_by_chain: dict[str, list[Candidate]]


class MatchDecision(BaseModel):
    index: int = Field(description="The index of the list item this decision is for")
    chain: str = Field(description="The chain slug")
    item_code: str | None = Field(description="The chosen candidate's item_code, or null when none fits")
    confidence: Literal["high", "low"] = Field(description="low when the shopper should confirm the choice")
    reason: str = Field(description="One short sentence, in English")


class MatchDecisions(BaseModel):
    decisions: list[MatchDecision]
