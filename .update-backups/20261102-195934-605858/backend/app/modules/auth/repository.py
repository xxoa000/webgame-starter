from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import User


def find_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))
