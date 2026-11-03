"""저장 모델과 데이터베이스 관계를 정의한다."""
from sqlalchemy import CheckConstraint, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (CheckConstraint("slot_capacity > 0", name="ck_inventory_slots"),
                      CheckConstraint("max_weight_grams > 0", name="ck_inventory_weight"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    character_id: Mapped[int] = mapped_column(ForeignKey("character.id", ondelete="CASCADE"), unique=True, comment='캐릭터 ID')
    slot_capacity: Mapped[int] = mapped_column(default=10, comment='최대 보관 종류 수')
    max_weight_grams: Mapped[int] = mapped_column(default=30000, comment='최대 수용 무게(g)')


class InventoryEntry(Base):
    __tablename__ = "inventory_entry"
    __table_args__ = (UniqueConstraint("inventory_id", "item_id", name="uq_inventory_entry"),
                      CheckConstraint("quantity > 0", name="ck_inventory_quantity"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id", ondelete="CASCADE"), comment='인벤토리 ID')
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), comment='아이템 ID')
    quantity: Mapped[int] = mapped_column(comment='보유 수량')
