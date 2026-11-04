"""인벤토리 소지량·무게와 물자 사용 가능 여부의 응답을 정의한다."""
from pydantic import BaseModel, Field


class InventoryItemResponse(BaseModel):
    usable: bool = False
    hp_restore: int = 0
    mp_restore: int = 0
    sell_price: int = 0
    item_id: int
    name: str
    description: str
    kind: str
    quantity: int
    weight_grams: int
    total_weight_grams: int


class InventoryResponse(BaseModel):
    money: int
    character_id: int
    slot_capacity: int
    used_slots: int
    max_weight_grams: int
    current_weight_grams: int
    items: list[InventoryItemResponse]


class InventoryAction(BaseModel):
    """아이템 수량과 ID를 엄격하게 검사한다."""
    model_config={'extra':'forbid'}
    item_id:int=Field(gt=0,strict=True)
    quantity:int=Field(default=1,ge=1,le=9999,strict=True)
