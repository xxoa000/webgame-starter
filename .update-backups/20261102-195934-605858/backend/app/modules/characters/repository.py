from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth.models import User
from .models import Character


def get_owned(db: Session, user_id: int):
    return db.scalar(select(Character).where(Character.user_id == user_id))


def lock_owned(db: Session, user_id: int):
    # Parent lock also serializes creation when the character doesn't exist yet.
    db.execute(select(User).where(User.id == user_id).with_for_update()).scalar_one()
    return db.scalar(select(Character).where(Character.user_id == user_id).with_for_update())


def name_exists(db: Session, key: str):
    # Deliberately never query the archive table.
    return db.scalar(select(Character.id).where(Character.name_key == key)) is not None
