"""공통 아이템 사전. 채집·전리품·조합 결과를 같은 ID 체계로 다룬다."""
from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Item(Base):
    __tablename__ = "item"
    __table_args__ = (CheckConstraint("weight_grams > 0", name="ck_item_weight"),)
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    name: Mapped[str] = mapped_column(String(100), unique=True, comment='이름')
    description: Mapped[str] = mapped_column(Text, comment='설명')
    weight_grams: Mapped[int] = mapped_column(comment='개당 무게(g)')
    kind: Mapped[str] = mapped_column(String(20), comment='아이템 분류')


class FarmingItem(Base):
    __tablename__ = "farming_item"
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key=True, comment='아이템 ID')


class DropItem(Base):
    __tablename__ = "drop_item"
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key=True, comment='아이템 ID')
