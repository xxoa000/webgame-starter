from typing import Literal
from pydantic import BaseModel, Field, field_validator
from .rules import MAX_REROLLS
from .names import clean_name

class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=24)
    gender: Literal["male", "female", "other"]
    age: int = Field(ge=10, le=17, strict=True)
    bio: str = Field(default="", max_length=500)
    @field_validator("name")
    @classmethod
    def trim(cls, value):
        if not value.strip():
            raise ValueError("이름을 입력해.")
        return clean_name(value)

class DeleteCharacterRequest(BaseModel):
    character_id: int = Field(gt=0, strict=True)
    name: str = Field(min_length=1, max_length=24)

def character_data(c):
    if not c:
        return None
    return {"id": c.id, "name": c.name, "gender": c.gender, "age": c.age, "bio": c.bio,
            "stats": c.stats, "status": c.status, "rerolls_used": c.rerolls,
            "rerolls_remaining": MAX_REROLLS-c.rerolls}
