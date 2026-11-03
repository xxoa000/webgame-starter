"""저장 데이터 조회와 잠금 처리를 담당한다."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import User


def find_by_username(db: Session, username: str) -> User | None:
    """로그인 아이디로 사용자 계정을 조회한다."""
    return db.scalar(select(User).where(User.username == username))
