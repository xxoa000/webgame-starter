from pydantic import BaseModel


class FarmingOptionResponse(BaseModel):
    item_id: int
    name: str
    weight_grams: int
    probability: float


class MapResponse(BaseModel):
    id: int
    name: str
    description: str
    empty_probability: float
    items: list[FarmingOptionResponse]
