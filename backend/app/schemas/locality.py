from pydantic import BaseModel

from app.schemas.catalog import StoreResponse


class LocalityResponse(BaseModel):
    code: str
    name_he: str
    name_en: str

    model_config = {"from_attributes": True}


class NearbyGroup(BaseModel):
    locality: LocalityResponse
    distance_km: float
    stores: list[StoreResponse]


class ChainBranches(BaseModel):
    chain_slug: str
    chain_name: str
    in_city: list[StoreResponse]
    nearby: list[NearbyGroup]


class HomeUpdate(BaseModel):
    home_locality_code: str | None
