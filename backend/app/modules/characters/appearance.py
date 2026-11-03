"""프로필 프리셋을 검증하고 기존 외형 JSON과의 호환성을 유지한다."""
from typing import Literal
from pydantic import BaseModel, ConfigDict

class Appearance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    preset: Literal["portrait_01", "portrait_02", "portrait_03", "portrait_04", "portrait_05", "portrait_06"] = "portrait_01"
    hair: Literal["crop", "bob", "wave", "pony"] = "bob"
    face: Literal["soft", "sharp", "round"] = "soft"
    skin: Literal["ivory", "peach", "tan", "brown", "deep"] = "peach"
    hair_color: Literal["black", "brown", "blond", "silver", "red", "blue"] = "black"
    jacket: Literal["olive", "navy", "sand", "wine", "gray"] = "olive"
    trousers: Literal["charcoal", "brown", "navy", "sand"] = "charcoal"

class AppearanceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    appearance: Appearance
