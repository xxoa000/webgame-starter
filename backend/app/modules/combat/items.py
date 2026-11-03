"""보유한 회복 물자를 원자적으로 소비하며 전투 중에는 반격 기회를 준다."""
from fastapi import HTTPException
from sqlalchemy import select
from ..items.models import Item
from ..inventory.models import InventoryEntry
from ..characters.vitals import recover, limits
from .rules import ITEM_EFFECTS


def use_item(db, character, inventory, item_id):
    """소유한 회복 물자를 소비하고 HP·MP 효과를 적용한다."""
    if character.status != 'ready' or character.hp_current <= 0:
        raise HTTPException(409, '사망한 피계약자는 회복할 수 없어.')
    row = db.execute(select(InventoryEntry, Item).join(Item, Item.id == InventoryEntry.item_id)
        .where(InventoryEntry.inventory_id == inventory.id, Item.id == item_id).with_for_update()).first()
    if not row or row[0].quantity < 1:
        raise HTTPException(409, '보유하지 않은 아이템이야.')
    entry, item = row
    effect = ITEM_EFFECTS.get(item.name)
    if effect is None:
        raise HTTPException(422, '사용할 수 없는 아이템이야.')
    hp, mp, _ = limits(character)
    if not ((effect[0] and character.hp_current < hp) or (effect[1] and character.mp_current < mp)):
        raise HTTPException(409, '이미 최대치야.')
    hp_gain, mp_gain = recover(character, *effect)
    entry.quantity -= 1
    if entry.quantity == 0:
        db.delete(entry)
    db.flush()
    return f'{item.name} 사용. HP +{hp_gain}, MP +{mp_gain}.'
