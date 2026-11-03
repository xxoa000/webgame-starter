"""저장 모델과 데이터베이스 관계를 정의한다."""
from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Map(Base):
    __tablename__ = "map"
    __table_args__ = (CheckConstraint("empty_weight > 0", name="ck_map_empty_weight"),)
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    name: Mapped[str] = mapped_column(String(80), unique=True, comment='이름')
    description: Mapped[str] = mapped_column(Text, comment='설명')
    empty_weight: Mapped[int] = mapped_column(default=70, comment='빈손 결과 추첨 가중치')


class MapFarmingItem(Base):
    __tablename__ = "map_farming_item"
    __table_args__ = (UniqueConstraint("map_id", "farming_item_id", name="uq_map_farming_item"),
                      CheckConstraint("weight > 0", name="ck_map_farming_weight"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    map_id: Mapped[int] = mapped_column(ForeignKey("map.id"), comment='맵 ID')
    farming_item_id: Mapped[int] = mapped_column(ForeignKey("farming_item.item_id"), comment='파밍 아이템 ID')
    weight: Mapped[int] = mapped_column(comment='추첨 가중치')


class MapMonster(Base):
    __tablename__ = "map_monster"
    __table_args__ = (UniqueConstraint("map_id", "monster_id", name="uq_map_monster"),
                      CheckConstraint("weight > 0", name="ck_map_monster_weight"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    map_id: Mapped[int] = mapped_column(ForeignKey("map.id"), comment='맵 ID')
    monster_id: Mapped[int] = mapped_column(ForeignKey("monster.id"), comment='몬스터 ID')
    weight: Mapped[int] = mapped_column(comment='추첨 가중치')
