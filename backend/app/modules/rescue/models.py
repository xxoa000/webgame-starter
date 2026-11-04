"""캐릭터별 최근 구조 요청과 NPC 도착 시각을 보존한다."""
from datetime import datetime
from sqlalchemy import ForeignKey, DateTime, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class RescueRequest(Base):
    __tablename__='rescue_request'
    __table_args__=(CheckConstraint("status IN ('waiting','rescued','abandoned')", name='ck_rescue_status'),)
    id: Mapped[int]=mapped_column(primary_key=True,comment='구조 요청 ID')
    character_id: Mapped[int]=mapped_column(ForeignKey('character.id',ondelete='CASCADE'),unique=True,comment='구조 대상 캐릭터 ID')
    map_id: Mapped[int]=mapped_column(ForeignKey('map.id'),comment='구조 대상 맵 ID')
    status: Mapped[str]=mapped_column(String(12),comment='waiting대기 rescued구조 abandoned포기')
    requested_at: Mapped[datetime]=mapped_column(DateTime,comment='구조 요청 시각(UTC)')
    due_at: Mapped[datetime]=mapped_column(DateTime,comment='NPC 구조 도착 시각(UTC)')
    helper_user_id: Mapped[int | None]=mapped_column(ForeignKey('users.id'),nullable=True,comment='구조한 사용자 ID, NPC는 NULL')
