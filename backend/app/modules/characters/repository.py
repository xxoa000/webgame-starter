"""저장 데이터 조회와 잠금 처리를 담당한다."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..users.models import User
from .models import Character


def get_owned(db: Session, user_id: int):
    """사용자 소유 캐릭터를 조회한다."""
    return db.scalar(select(Character).where(Character.user_id == user_id))


def lock_owned(db: Session, user_id: int):
    # Parent lock also serializes creation when the character doesn't exist yet.
    """사용자와 캐릭터 행을 잠가 변경 요청을 직렬화한다."""
    db.execute(select(User).where(User.id == user_id).with_for_update().execution_options(populate_existing=True)).scalar_one()
    return db.scalar(select(Character).where(Character.user_id == user_id).with_for_update().execution_options(populate_existing=True))


def name_exists(db: Session, key: str):
    # Deliberately never query the archive table.
    """현재 캐릭터 테이블에서 이름 중복을 검사한다."""
    return db.scalar(select(Character.id).where(Character.name_key == key)) is not None
