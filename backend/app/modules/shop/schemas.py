"""아이템 거래 요청에서 정수 ID·수량만 허용한다."""
from pydantic import BaseModel,Field
class TradeRequest(BaseModel):
    model_config={'extra':'forbid'}
    item_id:int=Field(gt=0,strict=True)
    quantity:int=Field(ge=1,le=99,strict=True)


from typing import Literal
class UpgradeRequest(BaseModel):
    """상품 코드와 수량만 받고 가격·효과는 클라이언트에서 받지 않는다."""
    model_config = {'extra': 'forbid'}
    code: Literal['bag_expansion', 'stat_point']
    quantity: int = Field(default=1, ge=1, le=99, strict=True)
