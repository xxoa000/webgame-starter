"""저장 데이터 조회와 잠금 처리를 담당한다."""
from sqlalchemy import select
from .models import Exploration


def get_session(db, character_id):
    """캐릭터 탐색 세션을 잠금 조회한다."""
    return db.scalar(select(Exploration).where(Exploration.character_id == character_id).with_for_update())
