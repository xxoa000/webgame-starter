from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...db import Base

class User(Base):
    __tablename__ = "client"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(24), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

class LoginSession(Base):
    __tablename__ = "login_session"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("client.id"), index=True)
    expires_at: Mapped[object] = mapped_column(DateTime)
