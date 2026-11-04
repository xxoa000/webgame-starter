"""아이템 등급과 섭취 가능 여부의 공통 API 계약을 정의한다."""
from typing import Literal
from pydantic import BaseModel


class ItemTraitsResponse(BaseModel):
    rarity: Literal['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic'] = 'common'
    edible: bool = False
