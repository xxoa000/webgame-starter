"""무게는 정수 gram으로 계산한다. 모든 변경은 소유 캐릭터 잠금 후 실행한다."""
from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..characters import repository as characters
from ..items.models import Item
from ..characters.vitals import sync
from .models import Inventory, InventoryEntry
from . import repository


def ready_character(db, user_id):
    """ 소유 캐릭터의 등록 상태를 확인하고 자원을 갱신한다. """

    character = characters.lock_owned(db, user_id)
    if not character or character.status != "ready":
        raise HTTPException(409, "캐릭터가 필요해.")
    sync(character)

    return character


def ensure_inventory(db: Session, character_id: int):
    """ 캐릭터 인벤토리가 없으면 기본 용량으로 생성한다. """

    inventory = repository.get_inventory(db, character_id)
    if inventory is None:
        inventory = Inventory(character_id=character_id, slot_capacity=10, max_weight_grams=30000)
        db.add(inventory)
        db.flush()

    return inventory


def inventory_data(db: Session, inventory):
    """ 소지품 수량과 총무게를 계산해 응답을 구성한다. """

    from ..combat.rules import ITEM_EFFECTS
    import math
    from ..characters.models import Character
    from ..users.models import User
    from ..characters.vitals import limits

    character=db.get(Character,inventory.character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="캐릭터를 찾을 수 없습니다.",)
    
    user = db.get(User, character.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.",)
    
    maximum_hp,maximum_mp,_=limits(character)

    from ..items.presentation import item_traits
    traits = item_traits(db)
    rows = repository.get_entries(db, inventory.id)

    items = [
        {
            **traits[item.id],
            "item_id": item.id,
            "name": item.name,
            "description": item.description,
            "hp_restore": math.ceil(maximum_hp*ITEM_EFFECTS.get(item.name,(0,0))[0]/100),
            "mp_restore": math.ceil(maximum_mp*ITEM_EFFECTS.get(item.name,(0,0))[1]/100),
            "sell_price":item.sell_price,
            "usable": item.name in ITEM_EFFECTS,
            "kind": item.kind,
            "quantity": entry.quantity,
            "weight_grams": item.weight_grams,
            "total_weight_grams": entry.quantity * item.weight_grams
        } for entry, item in rows
    ]

    return {
        "money": user.money,
        "character_id": inventory.character_id,
        "slot_capacity": inventory.slot_capacity,
        "used_slots": len(rows),
        "max_weight_grams": inventory.max_weight_grams,
        "current_weight_grams": sum(row["total_weight_grams"] for row in items),
        "items": items
    }


def get_inventory(db, user_id):
    """ 소유 캐릭터의 인벤토리를 조회한다. """

    character = ready_character(db, user_id)
    inventory = ensure_inventory(db, character.id)
    result = inventory_data(db, inventory)
    db.commit()

    return result


def add_item(db, inventory, item: Item, quantity: int):
    """ 종류 수와 무게 제한을 확인하고 소지품을 추가한다. """

    rows = repository.get_entries(db, inventory.id)
    existing = next((entry for entry, current in rows if current.id == item.id), None)

    if existing is None and len(rows) >= inventory.slot_capacity:
        raise HTTPException(
            409,
            f"인벤토리 {inventory.slot_capacity}칸이 가득 찼어. 기존 물품을 버리거나 포기해야 해."
        )
    total = sum(entry.quantity * current.weight_grams for entry, current in rows)

    if total + quantity * item.weight_grams > inventory.max_weight_grams:
        raise HTTPException(
            409,
            f"최대 무게 {inventory.max_weight_grams / 1000:g}kg 초과. 더 이상 들 수 없어."
        )
    
    if existing:
        existing.quantity += quantity
    else:
        db.add(InventoryEntry(inventory_id=inventory.id, item_id=item.id, quantity=quantity))
    db.flush()


def change_item(db,user_id,body,use=False):
    """ 회복은 턴 없이 적용, 버리기는 보유 수량 안에서만 처리한다. """

    from sqlalchemy import select
    from ..characters.vitals import require_mobile
    from ..combat.items import use_item
    from ..exploration.models import Exploration
    from ..exploration.service import append_event

    character=ready_character(db,user_id)
    require_mobile(character)
    inventory=ensure_inventory(db,character.id)

    session=db.scalar(
        select(Exploration)
        .where(Exploration.character_id==character.id).with_for_update()
    )

    if use:
        if body.quantity!=1:
            raise HTTPException(422,'회복 물품은 한 번에 하나씩 사용해.')
        message=use_item(db,character,inventory,body.item_id)
    else:
        entry=db.scalar(
            select(InventoryEntry)
            .where(
                InventoryEntry.inventory_id==inventory.id,
                InventoryEntry.item_id==body.item_id
            ).with_for_update()
        )
        if not entry or entry.quantity<body.quantity:
            raise HTTPException(409,'버릴 수량이 보유 수량보다 많아.')

        item=db.get(Item,body.item_id)
        message=f'{item.name} {body.quantity}개를 버렸다.'

        entry.quantity-=body.quantity
        if not entry.quantity:
            db.delete(entry)

    if session and session.status=='active':
        append_event(session,'item' if use else 'discard',message)
        session.version+=1

    db.flush()
    result=inventory_data(db,inventory)
    db.commit()

    return result
