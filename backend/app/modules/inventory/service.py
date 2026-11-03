"""무게는 정수 gram으로 계산한다. 모든 변경은 소유 캐릭터 잠금 후 실행한다."""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..characters import repository as characters
from ..items.models import Item
from ..characters.vitals import sync
from .models import Inventory, InventoryEntry
from . import repository


def ready_character(db, user_id):
    """소유 캐릭터의 등록 상태를 확인하고 자원을 갱신한다."""
    character = characters.lock_owned(db, user_id)
    if not character or character.status != "ready":
        raise HTTPException(409, "생성을 완료한 캐릭터가 필요해.")
    sync(character)
    return character


def ensure_inventory(db: Session, character_id: int):
    """캐릭터 인벤토리가 없으면 기본 용량으로 생성한다."""
    inventory = repository.get_inventory(db, character_id)
    if inventory is None:
        inventory = Inventory(character_id=character_id, slot_capacity=10, max_weight_grams=30000)
        db.add(inventory)
        db.flush()
    return inventory


def inventory_data(db: Session, inventory):
    """소지품 수량과 총무게를 계산해 응답을 구성한다."""
    from ..combat.rules import ITEM_EFFECTS
    rows = repository.get_entries(db, inventory.id)
    items = [{"item_id": item.id, "name": item.name, "description": item.description,
              "usable": item.name in ITEM_EFFECTS, "kind": item.kind, "quantity": entry.quantity, "weight_grams": item.weight_grams,
              "total_weight_grams": entry.quantity * item.weight_grams} for entry, item in rows]
    return {"character_id": inventory.character_id, "slot_capacity": inventory.slot_capacity,
            "used_slots": len(rows), "max_weight_grams": inventory.max_weight_grams,
            "current_weight_grams": sum(row["total_weight_grams"] for row in items), "items": items}


def get_inventory(db, user_id):
    """소유 캐릭터의 인벤토리를 조회한다."""
    character = ready_character(db, user_id)
    inventory = ensure_inventory(db, character.id)
    result = inventory_data(db, inventory)
    db.commit()
    return result


def add_item(db, inventory, item: Item, quantity: int):
    """종류 수와 무게 제한을 확인하고 소지품을 추가한다."""
    rows = repository.get_entries(db, inventory.id)
    existing = next((entry for entry, current in rows if current.id == item.id), None)
    if existing is None and len(rows) >= inventory.slot_capacity:
        raise HTTPException(409, "인벤토리 10칸이 가득 찼어. 발견한 아이템을 포기할 수 있어.")
    total = sum(entry.quantity * current.weight_grams for entry, current in rows)
    if total + quantity * item.weight_grams > inventory.max_weight_grams:
        raise HTTPException(409, "최대 무게 30kg을 초과해. 발견한 아이템을 포기할 수 있어.")
    if existing:
        existing.quantity += quantity
    else:
        db.add(InventoryEntry(inventory_id=inventory.id, item_id=item.id, quantity=quantity))
    db.flush()
