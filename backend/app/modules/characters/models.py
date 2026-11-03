"""현재·삭제된 피계약자의 저장 모델. 외형 JSON은 능력치와 별도로 보관한다."""
from datetime import datetime
from sqlalchemy import String, Integer, ForeignKey, JSON, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...database.base import Base

class Character(Base):
    __tablename__ = "character"
    __table_args__ = (CheckConstraint("rerolls >= 0 AND rerolls <= 10"),
                      CheckConstraint("gender IN ('male','female','other')"),
                      CheckConstraint("name_changes BETWEEN 0 AND 1 AND age_changes BETWEEN 0 AND 1", name="ck_character_profile_changes"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, comment='사용자 ID')
    name: Mapped[str] = mapped_column(String(24), default="", comment='이름')
    name_key: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, comment='이름 중복 검사 키')
    gender: Mapped[str] = mapped_column(String(12), default="male", comment='성별')
    age: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='나이(세)')
    bio: Mapped[str] = mapped_column(String(500), default="", comment='프로필 소개')
    appearance: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='프로필 프리셋 정보')
    stats: Mapped[dict] = mapped_column(JSON, comment='능력치 정보')
    rerolls: Mapped[int] = mapped_column(Integer, default=10, comment='남은 능력치 재추첨 횟수')
    hp_current: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='현재 HP')
    mp_current: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='현재 MP')
    stamina_current: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='현재 스태미나')
    stamina_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='스태미나 회복 기준 시각(UTC)')
    status: Mapped[str] = mapped_column(String(12), default="draft", comment='진행 상태')
    name_changes: Mapped[int] = mapped_column(Integer, default=0, server_default='0', comment='생성 후 이름 변경 횟수')
    age_changes: Mapped[int] = mapped_column(Integer, default=0, server_default='0', comment='생성 후 나이 변경 횟수')
    personality: Mapped[list['CharacterPersonality']] = relationship('CharacterPersonality', lazy='selectin', cascade='all, delete-orphan', passive_deletes=True)

class DeletedCharacter(Base):
    personality_snapshot: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="삭제 시 성격 선택 보관")
    __tablename__ = "deleted_character"
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    original_character_id: Mapped[int] = mapped_column(Integer, comment='원래 캐릭터 ID')
    # No UNIQUE: a user can have any number of deletion records.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, comment='사용자 ID')
    name: Mapped[str] = mapped_column(String(24), comment='이름')
    gender: Mapped[str] = mapped_column(String(12), comment='성별')
    age: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='나이(세)')
    bio: Mapped[str] = mapped_column(String(500), comment='프로필 소개')
    appearance: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='프로필 프리셋 정보')
    stats: Mapped[dict] = mapped_column(JSON, comment='능력치 정보')
    rerolls: Mapped[int] = mapped_column(Integer, comment='남은 능력치 재추첨 횟수')
    status: Mapped[str] = mapped_column(String(12), comment='진행 상태')
    deleted_at: Mapped[datetime] = mapped_column(DateTime, comment='삭제 또는 사망 시각(UTC)')
