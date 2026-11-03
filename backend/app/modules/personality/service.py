"""세 분류의 성격 선택을 검증하고 캐릭터에 한 번만 저장한다."""
from fastapi import HTTPException
from sqlalchemy import select
from .models import PersonalityKeyword, CharacterPersonality


def choices(db):
    """사용 가능한 키워드를 분류와 ID 순서로 반환한다."""
    return db.scalars(select(PersonalityKeyword).order_by(PersonalityKeyword.id)).all()


def validate_choices(db, keyword_ids):
    """서로 다른 세 키워드가 세 분류를 모두 포함하는지 검사한다."""
    if len(keyword_ids) != 3 or len(set(keyword_ids)) != 3:
        raise HTTPException(422, '겉성격·속성격·성향을 하나씩 선택해.')
    rows = db.scalars(select(PersonalityKeyword).where(PersonalityKeyword.id.in_(keyword_ids))).all()
    if len(rows) != 3 or {row.category for row in rows} != {'OUTER','INNER','ALIGNMENT'}:
        raise HTTPException(422, '성격 분류별로 하나씩 선택해야 해.')
    return rows


def assign(db, character, keyword_ids):
    """기존 선택을 덮어쓰지 않고 세 분류를 확정한다."""
    if character.personality:
        raise HTTPException(409, '이미 성격 선택이 완료됐어.')
    rows = validate_choices(db, keyword_ids)
    for row in rows:
        db.add(CharacterPersonality(character_id=character.id, category=row.category, keyword_id=row.id))
    db.flush()
    db.expire(character, ['personality'])


def snapshot(character):
    """현재 성격을 응답과 삭제 보관에 사용할 독립 데이터로 구성한다."""
    return [{'id':link.keyword_id,'category':link.category,'code':link.keyword.code,'name':link.keyword.name}
        for link in character.personality]
