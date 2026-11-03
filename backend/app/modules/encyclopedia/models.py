"""저장 모델과 데이터베이스 관계를 정의한다."""
from datetime import datetime
from sqlalchemy import ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Encyclopedia(Base):
    __tablename__ = 'encyclopedia'
    __table_args__ = (UniqueConstraint('character_id','item_id',name='uq_encyclopedia_character_item'),)
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    character_id: Mapped[int] = mapped_column(ForeignKey('character.id',ondelete='CASCADE'), comment='캐릭터 ID')
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'), comment='아이템 ID')
    first_map_id: Mapped[int | None] = mapped_column(ForeignKey('map.id'),nullable=True, comment='최초 발견 맵 ID')
    discovered_at: Mapped[datetime] = mapped_column(DateTime, comment='최초 발견 시각(UTC)')
