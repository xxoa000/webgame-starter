"""90초 이내의 접속 신호와 진행 상태로 맵별 탐사 인원을 집계한다."""
from datetime import timedelta
from sqlalchemy import select, func
from ...database.base import utc_now
from ..characters.models import Character
from ..users.models import User
from .models import Exploration, ExplorationPresence

PRESENCE_TTL_SECONDS = 90


def counts(db):
    """종료·사망·제재 계정을 제외하고 계정당 한 명만 집계한다."""
    cutoff = utc_now() - timedelta(seconds=PRESENCE_TTL_SECONDS)
    rows = db.execute(select(ExplorationPresence.map_id, func.count())
        .join(User, User.id == ExplorationPresence.user_id)
        .join(Character, Character.user_id == User.id)
        .join(Exploration, Exploration.character_id == Character.id)
        .where(ExplorationPresence.last_seen_at >= cutoff, User.user_status == 1,
               Character.status == 'ready', Character.downed.is_(False), Exploration.status == 'active',
               Exploration.map_id == ExplorationPresence.map_id)
        .group_by(ExplorationPresence.map_id)).all()
    return {"counts": {str(map_id): count for map_id, count in rows}, "ttl_seconds": PRESENCE_TTL_SECONDS}


def heartbeat(db, user_id):
    """인증된 계정의 실제 탐색 맵으로만 접속 신호를 갱신한다."""
    db.scalar(select(User).where(User.id == user_id).with_for_update())
    session = db.scalar(select(Exploration).join(Character, Character.id == Exploration.character_id)
        .where(Character.user_id == user_id, Character.status == 'ready', Character.downed.is_(False), Exploration.status == 'active'))
    row = db.get(ExplorationPresence, user_id)
    if session is None:
        if row is not None:
            db.delete(row)
    elif row is None:
        db.add(ExplorationPresence(user_id=user_id, map_id=session.map_id, last_seen_at=utc_now()))
    else:
        row.map_id, row.last_seen_at = session.map_id, utc_now()
    db.commit()
    return counts(db)
