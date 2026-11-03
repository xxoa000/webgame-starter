"""피계약자 생성·외형 수정·삭제와 보관 처리를 소유자 잠금 및 트랜잭션으로 수행한다."""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .rules import MAX_REROLLS
from ...core.security import now
from .names import name_key
from ..users.models import User
from .models import Character, DeletedCharacter
from .schemas import Profile, DeleteCharacterRequest, character_data
from .stats import roll
from .vitals import initialize
from . import repository
from ..personality import service as personality_service

def draft(user: User, db: Session):
    """생성 중인 캐릭터를 조회하거나 새로 생성한다."""
    c = repository.lock_owned(db, user.id)
    if c and c.status == 'dead':
        db.delete(c)
        db.flush()
        c = None
    if not c:
        c = Character(user_id=user.id, stats=roll(), rerolls=MAX_REROLLS, status="draft")
        db.add(c)
        db.commit()
    return character_data(c)

def reroll(user: User, db: Session):
    """남은 기회를 확인하고 캐릭터 능력치를 재추첨한다."""
    c = repository.lock_owned(db, user.id)
    if not c or c.status != "draft":
        raise HTTPException(409, "재추첨할 생성 중 캐릭터가 없어.")
    if c.rerolls <= 0:
        raise HTTPException(409, "재추첨 10회를 모두 사용했어.")
    c.stats = roll()
    c.rerolls -= 1
    db.commit()
    return character_data(c)

def finalize(body: Profile, user: User, db: Session):
    """프로필을 확정하고 초기 자원과 인벤토리를 생성한다."""
    c = repository.lock_owned(db, user.id)
    if not c or c.status != "draft":
        raise HTTPException(409, "확정할 생성 중 캐릭터가 없어.")
    personality_service.validate_choices(db, body.personality_keyword_ids)
    key = name_key(body.name)
    if repository.name_exists(db, key):
        raise HTTPException(409, "이미 사용 중인 캐릭터 이름이야.")
    c.name, c.name_key = body.name, key
    c.gender, c.age, c.bio, c.status = body.gender, body.age, body.bio, "ready"
    c.appearance = body.appearance.model_dump()
    initialize(c)
    try:
        # A completed character receives its inventory in the same transaction.
        from ..inventory.service import ensure_inventory
        db.flush()
        ensure_inventory(db, c.id)
        personality_service.assign(db, c, body.personality_keyword_ids)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용 중인 캐릭터 이름이야. 다시 확인해.")
    return character_data(c)

def delete_character(body: DeleteCharacterRequest, user: User, db: Session):
    """소유권과 이름 확인 후 캐릭터를 보관하고 삭제한다."""
    if user.auth != 9:
        raise HTTPException(403, '관리자만 캐릭터를 삭제할 수 있어.')
    owner_id = db.scalar(select(Character.user_id).where(Character.id == body.character_id))
    c = repository.lock_owned(db, owner_id) if owner_id is not None else None
    if not c or c.id != body.character_id:
        raise HTTPException(404, "삭제할 캐릭터를 찾을 수 없어. 화면을 새로고침해.")
    if c.status != "ready":
        raise HTTPException(409, "생성이 완료된 캐릭터만 삭제할 수 있어.")
    # Confirmation must match the displayed name exactly, including case/spaces.
    if body.name != c.name:
        raise HTTPException(422, "캐릭터 이름이 일치하지 않아.")
    archive = DeletedCharacter(personality_snapshot=personality_service.snapshot(c), original_character_id=c.id, user_id=c.user_id,
        name=c.name, gender=c.gender, age=c.age, bio=c.bio, appearance=dict(c.appearance or {}), stats=dict(c.stats),
        rerolls=c.rerolls, status=c.status, deleted_at=now())
    db.add(archive)
    db.flush()  # Do not remove the live row if the archive cannot be inserted.
    db.delete(c)
    db.commit()  # Archive insertion and live deletion commit atomically.
    return {"message": "캐릭터를 삭제했어."}


def update_appearance(body, user: User, db: Session):
    """능력치와 성별을 유지하며 프로필 프리셋을 저장한다."""
    c = repository.lock_owned(db, user.id)
    if not c or c.status != "ready":
        raise HTTPException(409, "등록 완료된 피계약자가 필요해.")
    c.appearance = body.appearance.model_dump()
    db.commit()
    return character_data(c)


def update_profile(body, user, db):
    """이름과 나이는 각각 한 번, 성별과 소개는 제한 없이 갱신한다."""
    c = repository.lock_owned(db, user.id)
    if not c or c.status != 'ready':
        raise HTTPException(409, '등록 완료된 피계약자가 필요해.')
    values = body.model_dump(exclude_unset=True)
    if not values:
        raise HTTPException(422, '변경할 내용을 입력해.')
    if 'name' in values and values['name'] != c.name:
        if c.name_changes >= 1:
            raise HTTPException(409, '이름 수정 기회를 이미 사용했어.')
        key = name_key(values['name'])
        if key != c.name_key and repository.name_exists(db, key):
            raise HTTPException(409, '이미 사용 중인 캐릭터 이름이야.')
        c.name, c.name_key, c.name_changes = values['name'], key, c.name_changes+1
    if 'age' in values and values['age'] != c.age:
        if c.age_changes >= 1:
            raise HTTPException(409, '나이 수정 기회를 이미 사용했어.')
        c.age, c.age_changes = values['age'], c.age_changes+1
    for key in ('gender','bio'):
        if key in values:
            setattr(c, key, values[key])
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, '이미 사용 중인 캐릭터 이름이야.')
    return character_data(c)


def select_personality(body, user, db):
    """이전 캐릭터의 비어 있는 성격 선택만 한 번 확정한다."""
    c = repository.lock_owned(db, user.id)
    if not c or c.status != 'ready':
        raise HTTPException(409, '등록 완료된 피계약자가 필요해.')
    personality_service.assign(db, c, body.personality_keyword_ids)
    db.commit()
    return character_data(c)
