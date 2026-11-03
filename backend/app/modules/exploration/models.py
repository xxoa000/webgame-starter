"""탐색 턴·발견 물자·진행 중인 전투를 영속화한다."""
from sqlalchemy import CheckConstraint, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Exploration(Base):
    __tablename__ = "exploration"
    __table_args__ = (CheckConstraint("turn >= 0 AND version > 0", name="ck_exploration_counters"),
                      CheckConstraint("status IN ('active', 'ended')", name="ck_exploration_status"),
                      CheckConstraint("(pending_item_id IS NULL AND pending_quantity = 0) OR (pending_item_id IS NOT NULL AND pending_quantity > 0)", name="ck_exploration_pending"), {"sqlite_autoincrement": True})
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    character_id: Mapped[int] = mapped_column(ForeignKey("character.id", ondelete="CASCADE"), unique=True, comment='캐릭터 ID')
    map_id: Mapped[int] = mapped_column(ForeignKey("map.id"), comment='맵 ID')
    status: Mapped[str] = mapped_column(String(16), default="active", comment='진행 상태')
    turn: Mapped[int] = mapped_column(default=0, comment='진행 턴 수')
    version: Mapped[int] = mapped_column(default=1, comment='동시 요청 검증 번호')
    pending_item_id: Mapped[int | None] = mapped_column(ForeignKey("item.id"), nullable=True, comment='회수 대기 아이템 ID')
    pending_quantity: Mapped[int] = mapped_column(default=0, comment='회수 대기 수량')
    combat: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='진행 중인 전투 상태')
    history: Mapped[list] = mapped_column(JSON, default=list, comment='최근 탐색 기록')
