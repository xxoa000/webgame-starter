from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...db import Base

class Character(Base):
    __tablename__ = "character"
    __table_args__ = (CheckConstraint("rerolls >= 0 AND rerolls <= 10"),
                      CheckConstraint("gender IN ('male','female','other')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("client.id"), unique=True)
    name: Mapped[str] = mapped_column(String(24), default="")
    name_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    gender: Mapped[str] = mapped_column(String(12), default="other")
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bio: Mapped[str] = mapped_column(String(500), default="")
    stats: Mapped[dict] = mapped_column(JSON)
    rerolls: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(12), default="draft")

class DeletedCharacter(Base):
    __tablename__ = "deleted_character"
    id: Mapped[int] = mapped_column(primary_key=True)
    original_character_id: Mapped[int] = mapped_column(Integer)
    # No UNIQUE: a user can have any number of deletion records.
    user_id: Mapped[int] = mapped_column(ForeignKey("client.id"), index=True)
    name: Mapped[str] = mapped_column(String(24))
    gender: Mapped[str] = mapped_column(String(12))
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bio: Mapped[str] = mapped_column(String(500))
    stats: Mapped[dict] = mapped_column(JSON)
    rerolls: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(12))
    deleted_at: Mapped[datetime] = mapped_column(DateTime)
