"""저장 데이터 조회와 잠금 처리를 담당한다."""
from sqlalchemy import select
from .models import Encyclopedia
from ...core.security import now


def known_ids(db, character_id):
    """캐릭터가 발견한 아이템 ID를 조회한다."""
    return set(db.scalars(select(Encyclopedia.item_id).where(Encyclopedia.character_id==character_id)))


def discover(db, character_id, item_id, map_id):
    # Caller holds character lock, serializing every discovery for this owner.
    """최초 발견한 아이템을 캐릭터 도감에 기록한다."""
    if item_id not in known_ids(db,character_id):
        db.add(Encyclopedia(character_id=character_id,item_id=item_id,first_map_id=map_id,discovered_at=now()))
        db.flush()
