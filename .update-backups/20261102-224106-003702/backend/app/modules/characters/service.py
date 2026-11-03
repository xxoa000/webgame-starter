"""Character lifecycle and transaction boundaries live here."""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .rules import MAX_REROLLS
from ...core.security import now
from .names import name_key
from ..users.models import User
from .models import Character, DeletedCharacter
from .schemas import Profile, DeleteCharacterRequest, character_data
from .stats import roll
from . import repository

def draft(user: User, db: Session):
    c = repository.lock_owned(db, user.id)
    if not c:
        c = Character(user_id=user.id, stats=roll(), rerolls=0, status="draft")
        db.add(c)
        db.commit()
    return character_data(c)

def reroll(user: User, db: Session):
    c = repository.lock_owned(db, user.id)
    if not c or c.status != "draft":
        raise HTTPException(409, "재추첨할 생성 중 캐릭터가 없어.")
    if c.rerolls >= MAX_REROLLS:
        raise HTTPException(409, "재추첨 10회를 모두 사용했어.")
    c.stats = roll()
    c.rerolls += 1
    db.commit()
    return character_data(c)

def finalize(body: Profile, user: User, db: Session):
    c = repository.lock_owned(db, user.id)
    if not c or c.status != "draft":
        raise HTTPException(409, "확정할 생성 중 캐릭터가 없어.")
    key = name_key(body.name)
    if repository.name_exists(db, key):
        raise HTTPException(409, "이미 사용 중인 캐릭터 이름이야.")
    c.name, c.name_key = body.name, key
    c.gender, c.age, c.bio, c.status = body.gender, body.age, body.bio, "ready"
    try:
        # A completed character receives its inventory in the same transaction.
        from ..inventory.service import ensure_inventory
        db.flush()
        ensure_inventory(db, c.id)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용 중인 캐릭터 이름이야. 다시 확인해.")
    return character_data(c)

def delete_character(body: DeleteCharacterRequest, user: User, db: Session):
    c = repository.lock_owned(db, user.id)
    if not c or c.id != body.character_id:
        raise HTTPException(404, "삭제할 캐릭터를 찾을 수 없어. 화면을 새로고침해.")
    if c.status != "ready":
        raise HTTPException(409, "생성이 완료된 캐릭터만 삭제할 수 있어.")
    # Confirmation must match the displayed name exactly, including case/spaces.
    if body.name != c.name:
        raise HTTPException(422, "캐릭터 이름이 일치하지 않아.")
    archive = DeletedCharacter(original_character_id=c.id, user_id=c.user_id,
        name=c.name, gender=c.gender, age=c.age, bio=c.bio, stats=dict(c.stats),
        rerolls=c.rerolls, status=c.status, deleted_at=now())
    db.add(archive)
    db.flush()  # Do not remove the live row if the archive cannot be inserted.
    db.delete(c)
    db.commit()  # Archive insertion and live deletion commit atomically.
    return {"message": "캐릭터를 삭제했어."}
