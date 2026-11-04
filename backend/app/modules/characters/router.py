"""인증된 사용자의 피계약자 생성·조회·외형 수정·삭제 API를 연결한다."""
from typing import Annotated
from fastapi import APIRouter, HTTPException
from pydantic import Field
from ...core.dependencies import DB
from ...core.security import Auth
from .rules import STAT_RANGES, MAX_REROLLS, STAT_TOTAL
from .names import clean_name, name_key
from .appearance import AppearanceUpdate
from .schemas import Profile, DeleteCharacterRequest, character_data, ProfileUpdate, PersonalitySelection
from . import repository, service, vitals

router = APIRouter(tags=["characters"])


@router.get("/me")
def me(user: Auth, db: DB):
    """현재 사용자 정보와 소유 캐릭터를 반환한다."""
    character = repository.lock_owned(db, user.id)
    if character and character.status == 'ready':
        vitals.sync(character)
    result = {"money": user.money, "username": user.username, "auth": user.auth, "user_status": user.user_status, "character": character_data(character)}
    db.commit()
    return result


@router.get("/characters/rules")
def rules():
    """캐릭터 생성 제한과 능력치 범위를 반환한다."""
    return {"ranges": STAT_RANGES, "max_rerolls": MAX_REROLLS, "stat_total": STAT_TOTAL}


@router.get("/characters/check-name")
def check_name(name: Annotated[str, Field(min_length=1, max_length=24)], user: Auth, db: DB, for_profile: bool = False):
    """캐릭터 이름의 사용 가능 여부를 검사한다."""
    if not clean_name(name):
        raise HTTPException(422, "이름을 입력해.")
    key = name_key(name)
    own = repository.get_owned(db, user.id) if for_profile else None
    same_owner = own is not None and own.status == 'ready' and own.name_key == key
    return {"available": same_owner or not repository.name_exists(db, key)}


@router.post("/characters/draft")
def draft(user: Auth, db: DB):
    """생성 중인 캐릭터를 조회하거나 새로 생성한다."""
    return service.draft(user, db)


@router.post("/characters/reroll")
def reroll(user: Auth, db: DB):
    """남은 기회를 확인하고 캐릭터 능력치를 재추첨한다."""
    return service.reroll(user, db)


@router.post("/characters/finalize")
def finalize(body: Profile, user: Auth, db: DB):
    """프로필을 확정하고 초기 자원과 인벤토리를 생성한다."""
    return service.finalize(body, user, db)


@router.post("/characters/delete")
def delete(body: DeleteCharacterRequest, user: Auth, db: DB):
    """이름 확인을 거쳐 소유 캐릭터를 삭제한다."""
    return service.delete_character(body, user, db)


@router.get('/characters/vitals')
def get_vitals(user: Auth, db: DB):
    """캐릭터 자원을 동기화해 반환한다."""
    from ..inventory.service import ready_character
    character = ready_character(db, user.id)
    result = vitals.data(character)
    db.commit()
    return result


@router.post("/characters/appearance")
def update_appearance(body: AppearanceUpdate, user: Auth, db: DB):
    """능력치와 성별을 유지하며 프로필 프리셋을 저장한다."""
    return service.update_appearance(body, user, db)


@router.patch('/characters/profile')
def update_profile(body: ProfileUpdate, user: Auth, db: DB):
    """사용자 소유 캐릭터의 인적사항을 수정한다."""
    return service.update_profile(body, user, db)


@router.post('/characters/personality')
def select_personality(body: PersonalitySelection, user: Auth, db: DB):
    """기존 캐릭터의 최초 성격 선택을 저장한다."""
    return service.select_personality(body, user, db)


from .allocation import StatAllocation, allocate


@router.post('/characters/stats/allocate')
def allocate_stats(body: StatAllocation, user: Auth, db: DB):
    """소유 캐릭터의 미분배 스탯 포인트를 확정한다."""
    return allocate(db, user.id, body)
