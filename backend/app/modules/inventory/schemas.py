"""인벤토리 소지량·무게와 물자 사용 가능 여부의 응답을 정의한다."""
from pydantic import BaseModel


class InventoryItemResponse(BaseModel):
    usable: bool = False
    item_id: int
    name: str
    description: str
    kind: str
    quantity: int
    weight_grams: int
    total_weight_grams: int


class InventoryResponse(BaseModel):
    character_id: int
    slot_capacity: int
    used_slots: int
    max_weight_grams: int
    current_weight_grams: int
    items: list[InventoryItemResponse]
