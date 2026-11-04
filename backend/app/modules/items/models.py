"""공통 아이템 사전. 채집·전리품·조합 결과를 같은 ID 체계로 다룬다."""
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Item(Base):
    __tablename__ = "item"
    __table_args__ = (CheckConstraint("weight_grams > 0", name="ck_item_weight"), CheckConstraint('buy_price >= 0 AND sell_price >= 0 AND (buy_price = 0 OR sell_price <= buy_price)', name='ck_item_prices'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    name: Mapped[str] = mapped_column(String(100), unique=True, comment='이름')
    description: Mapped[str] = mapped_column(Text, comment='설명')
    weight_grams: Mapped[int] = mapped_column(comment='개당 무게(g)')
    buy_price: Mapped[int] = mapped_column(default=0, server_default='0', comment='구매 가격, 0이면 상점 미판매')
    sell_price: Mapped[int] = mapped_column(default=10, server_default='10', comment='판매 가격, 무료 크레딧')
    edible: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0', comment='섭취 가능한 식음료 여부')
    is_event: Mapped[bool] = mapped_column(Boolean, default=False, server_default='0', comment='이벤트 전용 아이템 여부')
    kind: Mapped[str] = mapped_column(String(20), comment='아이템 분류')


class FarmingItem(Base):
    __tablename__ = "farming_item"
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key=True, comment='아이템 ID')


class DropItem(Base):
    __tablename__ = "drop_item"
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), primary_key=True, comment='아이템 ID')
