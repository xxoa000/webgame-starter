"""맵별 몬스터 조우와 전리품 확률 정보를 조회한다."""
from sqlalchemy import select
from ..maps.models import MapMonster
from ..monsters.models import Monster, MonsterDropItem
from ..items.models import Item


def monster_options(db, map_id):
    """맵에 연결된 몬스터와 출현 가중치를 조회한다."""
    return db.execute(select(MapMonster, Monster).join(Monster, Monster.id == MapMonster.monster_id)
        .where(MapMonster.map_id == map_id).order_by(MapMonster.id)).all()


def drop_options(db, monster_id):
    """몬스터에 연결된 전리품과 추첨 가중치를 조회한다."""
    return db.execute(select(MonsterDropItem, Item).join(Item, Item.id == MonsterDropItem.drop_item_id)
        .where(MonsterDropItem.monster_id == monster_id).order_by(MonsterDropItem.id)).all()
