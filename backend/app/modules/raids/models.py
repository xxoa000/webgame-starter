"""이벤트 일정·공유 보스·개인 수집량과 보상 기록을 보존한다."""
from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class RaidCycle(Base):
    __tablename__ = 'raid_cycle'
    id: Mapped[int] = mapped_column(primary_key=True, comment='전역 일정 잠금 ID')
    next_at: Mapped[datetime] = mapped_column(DateTime, comment='다음 이벤트 시작 가능 시각(UTC)')


class RaidEvent(Base):
    __tablename__ = 'raid_event'
    __table_args__ = (
        CheckConstraint("status IN ('collecting','boss','closed')", name='ck_raid_status'),
        CheckConstraint('collected >= 0 AND threshold > 0 AND boss_hp >= 0 AND boss_hp <= boss_max_hp AND boss_max_hp > 0 AND version > 0', name='ck_raid_counters'),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment='균열 이벤트 ID')
    map_id: Mapped[int] = mapped_column(ForeignKey('map.id'), comment='이벤트 지역')
    item_id: Mapped[int] = mapped_column(ForeignKey('item.id'), comment='이벤트 전용 물자')
    status: Mapped[str] = mapped_column(String(16), default='collecting', comment='수집·보스·종료 단계')
    collected: Mapped[int] = mapped_column(default=0, comment='지역 전체 누적 회수량')
    threshold: Mapped[int] = mapped_column(comment='보스 등장에 필요한 회수량')
    boss_hp: Mapped[int] = mapped_column(comment='모든 참가자가 공유하는 보스 HP')
    boss_max_hp: Mapped[int] = mapped_column(comment='보스 최대 HP')
    version: Mapped[int] = mapped_column(default=1, comment='중복·오래된 공격 차단 버전')
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='종료·보상 정산 시각(UTC)')


class RaidMember(Base):
    __tablename__ = 'raid_member'
    __table_args__ = (
        UniqueConstraint('event_id', 'character_id', name='uq_raid_member'),
        CheckConstraint('items >= 0 AND damage >= 0 AND reward >= 0', name='ck_raid_member_counters'),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment='기여 기록 ID')
    event_id: Mapped[int] = mapped_column(ForeignKey('raid_event.id'), comment='균열 이벤트 ID')
    character_id: Mapped[int | None] = mapped_column(ForeignKey('character.id', ondelete='SET NULL'), nullable=True, comment='참가 캐릭터, 삭제 시 기록 보존')
    name: Mapped[str] = mapped_column(String(24), comment='참가 당시 캐릭터 이름')
    items: Mapped[int] = mapped_column(default=0, comment='회수해 전용 보관 중인 물자 수')
    damage: Mapped[int] = mapped_column(default=0, comment='실제 보스 누적 피해량')
    reward: Mapped[int] = mapped_column(default=0, comment='정산한 스탯 포인트')
