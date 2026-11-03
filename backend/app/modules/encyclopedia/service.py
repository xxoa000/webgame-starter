"""기능별 업무 규칙과 트랜잭션을 처리한다."""
from ..characters.repository import get_owned
from .repository import known_ids


def known_for_user(db,user_id):
    """사용자 캐릭터의 발견 아이템 ID를 조회한다."""
    character=get_owned(db,user_id)
    return known_ids(db,character.id) if character else set()
