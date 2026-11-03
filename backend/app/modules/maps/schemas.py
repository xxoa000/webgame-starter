"""맵별 물자와 몬스터의 출현 확률 응답을 정의한다."""
from pydantic import BaseModel


class FarmingOptionResponse(BaseModel):
    item_id: int
    name: str
    discovered: bool
    weight_grams: int | None
    probability: float


class MonsterOptionResponse(BaseModel):
    name: str
    probability: float


class MapResponse(BaseModel):
    monsters: list[MonsterOptionResponse] = []
    id: int
    name: str
    description: str
    empty_probability: float
    items: list[FarmingOptionResponse]
