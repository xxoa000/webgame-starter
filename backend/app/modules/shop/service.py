"""무료 크레딧으로 아이템을 구매·판매하며 잔액과 인벤토리를 함께 반영한다."""
from fastapi import HTTPException
from sqlalchemy import select
from ..items.models import Item
from ..users.models import User
from ..inventory.service import ready_character,ensure_inventory,add_item,inventory_data
from ..inventory.models import InventoryEntry
from ..characters.vitals import require_mobile
from ..exploration.models import Exploration


def catalog(db,user_id):
    """서버에 등록된 판매 물품과 실제 가격을 반환한다."""
    ready_character(db,user_id)
    from ..items.presentation import item_traits
    traits = item_traits(db)
    rows=db.scalars(select(Item).where(Item.buy_price>0).order_by(Item.id)).all()
    return [{**traits[item.id], 'item_id':item.id,'name':item.name,'description':item.description,'buy_price':item.buy_price,
             'sell_price':item.sell_price,'weight_grams':item.weight_grams} for item in rows]


def trade(db,user_id,body,buy):
    """소유자 잠금 후 가격·잔액·수량·무게를 검증하고 한 번에 거래한다."""
    character=ready_character(db,user_id)
    require_mobile(character)
    session=db.scalar(select(Exploration).where(Exploration.character_id==character.id))
    if session and session.combat:
        raise HTTPException(409,'전투를 마친 뒤 거래할 수 있어.')
    inventory=ensure_inventory(db,character.id)
    user=db.get(User,user_id)
    item=db.scalar(select(Item).where(Item.id==body.item_id).with_for_update())
    if not item:
        raise HTTPException(404,'존재하지 않는 물품이야.')
    if buy:
        if item.buy_price<=0:
            raise HTTPException(409,'상점에서 판매하지 않는 물품이야.')
        cost=item.buy_price*body.quantity
        if user.money<cost:
            raise HTTPException(409,'크레딧이 부족해.')
        add_item(db,inventory,item,body.quantity)
        user.money-=cost
    else:
        entry=db.scalar(select(InventoryEntry).where(InventoryEntry.inventory_id==inventory.id,InventoryEntry.item_id==item.id).with_for_update())
        if not entry or entry.quantity<body.quantity or item.sell_price<=0:
            raise HTTPException(409,'판매 수량이나 판매 가능 여부를 확인해.')
        gain=item.sell_price*body.quantity
        if user.money+gain>2_000_000_000:
            raise HTTPException(409,'보유 크레딧 한도를 초과해.')
        entry.quantity-=body.quantity
        if not entry.quantity:
            db.delete(entry)
        user.money+=gain
    db.flush()
    result=inventory_data(db,inventory)
    db.commit()
    return result



def upgrades(db, user_id):
    """서버 가격을 가진 영구 확장 상품을 조회한다."""
    from .models import ShopUpgrade
    ready_character(db, user_id)
    return [{'code': row.code, 'name': row.name, 'description': row.description, 'price': row.price}
            for row in db.scalars(select(ShopUpgrade).order_by(ShopUpgrade.code))]


def buy_upgrade(db, user_id, body):
    """잔액 차감과 영구 효과를 소유자 잠금 아래 한 트랜잭션으로 적용한다."""
    from .models import ShopUpgrade
    character = ready_character(db, user_id)
    require_mobile(character)
    session = db.scalar(select(Exploration).where(Exploration.character_id == character.id))
    if session and session.combat:
        raise HTTPException(409, '전투를 마친 뒤 구매할 수 있어.')
    product = db.scalar(select(ShopUpgrade).where(ShopUpgrade.code == body.code).with_for_update())
    if not product:
        raise HTTPException(404, '판매 중인 상품이 없어.')
    user = db.get(User, user_id)
    cost = product.price * body.quantity
    if user.money < cost:
        raise HTTPException(409, '크레딧이 부족해.')
    inventory = ensure_inventory(db, character.id)
    if body.code == 'bag_expansion':
        if inventory.max_weight_grams + 10000 * body.quantity > 2_000_000_000:
            raise HTTPException(409, '보관 용량 한도를 초과해.')
        inventory.slot_capacity += body.quantity
        inventory.max_weight_grams += 10000 * body.quantity
    else:
        if character.stat_points + body.quantity > 2_000_000_000:
            raise HTTPException(409, '보유 포인트 한도를 초과해.')
        character.stat_points += body.quantity
        character.stat_version += 1
    user.money -= cost
    db.flush()
    result = inventory_data(db, inventory)
    db.commit()
    return result
