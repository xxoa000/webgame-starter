"""미분배 포인트만 소모하여 능력치를 올린다. 기존 능력치 환불은 허용하지 않는다."""
from typing import Annotated
from pydantic import BaseModel, Field
from fastapi import HTTPException
from sqlalchemy import select
from .schemas import character_data
from .vitals import require_mobile, sync
from ..inventory.service import ready_character
from ..exploration.models import Exploration

Point = Annotated[int, Field(ge=0, le=2_000_000_000, strict=True)]

class StatAllocation(BaseModel):
    """다섯 능력치의 추가 분배량과 화면에서 읽은 버전을 검증한다."""
    model_config = {'extra': 'forbid'}
    version: Point
    strength: Point = 0
    stamina: Point = 0
    intelligence: Point = 0
    agility: Point = 0
    luck: Point = 0


def allocate(db, user_id, body):
    """중복·변조·포인트 부족을 검사하고 능력치와 남은 포인트를 원자적으로 저장한다."""
    character = ready_character(db, user_id)
    require_mobile(character)
    session = db.scalar(select(Exploration).where(Exploration.character_id == character.id))
    if session and session.status == 'active':
        raise HTTPException(409, '탐색을 종료한 뒤 능력치를 분배해.')
    if character.stat_version != body.version:
        raise HTTPException(409, '포인트가 변경됐어. 최신 상태를 다시 확인해.')
    additions = body.model_dump(exclude={'version'})
    cost = sum(additions.values())
    if cost < 1 or cost > character.stat_points:
        raise HTTPException(409, '사용할 스탯 포인트가 부족해.')
    character.stats = {**character.stats, **{key: character.stats[key] + value for key, value in additions.items()}}
    character.stat_points -= cost
    character.stat_version += 1
    sync(character)  # 최대치만 늘린다. 구매·분배로 현재 자원을 무료 회복시키지 않는다.
    result = character_data(character)
    db.commit()
    return result
