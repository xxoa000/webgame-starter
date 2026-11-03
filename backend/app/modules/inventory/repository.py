"""저장 데이터 조회와 잠금 처리를 담당한다."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import Inventory, InventoryEntry
from ..items.models import Item


def get_inventory(db: Session, character_id: int):
    """소유 캐릭터의 인벤토리를 조회한다."""
    return db.scalar(select(Inventory).where(Inventory.character_id == character_id).with_for_update())


def get_entries(db: Session, inventory_id: int):
    # Lock entries to get current reads under MySQL REPEATABLE READ.
    """인벤토리의 소지품과 아이템 정보를 조회한다."""
    entries = db.scalars(select(InventoryEntry).where(InventoryEntry.inventory_id == inventory_id)
        .order_by(InventoryEntry.id).with_for_update()).all()
    return [(entry, db.get(Item, entry.item_id)) for entry in entries]
