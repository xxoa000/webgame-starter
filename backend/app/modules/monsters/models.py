"""향후 전투용 테이블만 정의한다. 현재 탐색에는 몬스터가 출현하지 않는다."""
from sqlalchemy import CheckConstraint, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Monster(Base):
    __tablename__ = "monster"
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    name: Mapped[str] = mapped_column(String(100), unique=True, comment='이름')
    description: Mapped[str] = mapped_column(Text, comment='설명')
    hp: Mapped[int] = mapped_column(default=20, comment='최대 HP')
    attack_min: Mapped[int] = mapped_column(default=2, comment='최소 공격력')
    attack_max: Mapped[int] = mapped_column(default=5, comment='최대 공격력')
    defense: Mapped[int] = mapped_column(default=0, comment='방어력')


class MonsterDropItem(Base):
    __tablename__ = "monster_drop_item"
    __table_args__ = (UniqueConstraint("monster_id", "drop_item_id", name="uq_monster_drop_item"),
                      CheckConstraint("weight > 0", name="ck_monster_drop_weight"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    monster_id: Mapped[int] = mapped_column(ForeignKey("monster.id"), comment='몬스터 ID')
    drop_item_id: Mapped[int] = mapped_column(ForeignKey("drop_item.item_id"), comment='전리품 아이템 ID')
    weight: Mapped[int] = mapped_column(comment='추첨 가중치')
