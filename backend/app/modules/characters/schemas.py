"""피계약자 등록·삭제 요청을 검증하고 외형·자원을 포함한 응답을 구성한다."""
from typing import Literal
from pydantic import BaseModel, Field, field_validator, StrictInt
from .appearance import Appearance
from .rules import MAX_REROLLS
from .vitals import data as vitals_data
from .names import clean_name
from ..personality.service import snapshot

class Profile(BaseModel):
    personality_keyword_ids: list[StrictInt] = Field(min_length=3, max_length=3)
    name: str = Field(min_length=1, max_length=24)
    gender: Literal["male", "female"]
    age: int = Field(ge=10, le=50, strict=True)
    bio: str = Field(default="", max_length=500)
    appearance: Appearance = Field(default_factory=Appearance)
    @field_validator("name")
    @classmethod
    def trim(cls, value):
        """캐릭터 이름의 공백과 표기를 정규화한다."""
        if not value.strip():
            raise ValueError("이름을 입력해.")
        return clean_name(value)

class DeleteCharacterRequest(BaseModel):
    character_id: int = Field(gt=0, strict=True)
    name: str = Field(min_length=1, max_length=24)

def character_data(c):
    """캐릭터 프로필과 능력치·자원을 응답 형식으로 구성한다."""
    if not c:
        return None
    return {"downed": c.downed, "id": c.id, "name": c.name, "gender": c.gender, "age": c.age, "bio": c.bio,
            "personality": snapshot(c), "name_changes_remaining": 1-c.name_changes, "age_changes_remaining": 1-c.age_changes,
            "stat_points": c.stat_points, "stat_version": c.stat_version, "appearance": Appearance.model_validate(c.appearance or {}).model_dump(), "stats": c.stats, "status": c.status, "rerolls_used": MAX_REROLLS-c.rerolls,
            "rerolls_remaining": c.rerolls, "vitals": vitals_data(c)}


class ProfileUpdate(BaseModel):
    """변경 기회를 조작하지 못하도록 수정 가능한 인적사항만 허용한다."""
    model_config = {"extra": "forbid"}
    name: str | None = Field(default=None, min_length=1, max_length=24)
    age: int | None = Field(default=None, ge=10, le=50, strict=True)
    gender: Literal['male','female'] | None = None
    bio: str | None = Field(default=None, max_length=500)

    @field_validator('name','age','gender','bio', mode='before')
    @classmethod
    def reject_null(cls, value):
        """명시적 NULL 저장을 거부한다."""
        if value is None:
            raise ValueError('값을 입력해.')
        return value

    @field_validator('name')
    @classmethod
    def normalize_name(cls, value):
        """변경 이름을 생성 시와 같은 기준으로 정규화한다."""
        if not value.strip():
            raise ValueError('이름을 입력해.')
        return clean_name(value)


class PersonalitySelection(BaseModel):
    """기존 캐릭터가 최초 성격 선택을 완료하는 요청이다."""
    model_config = {"extra": "forbid"}
    personality_keyword_ids: list[StrictInt] = Field(min_length=3, max_length=3)
