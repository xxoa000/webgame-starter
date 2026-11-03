"""저장 데이터 조회와 잠금 처리를 담당한다."""
from sqlalchemy import select
from .models import Map, MapFarmingItem
from ..items.models import Item


def list_maps(db):
    """공개 맵 목록과 발견 가능한 물자 확률을 조회한다."""
    return db.scalars(select(Map).order_by(Map.id)).all()


def farming_options(db, map_id):
    """맵에 연결된 파밍 아이템과 가중치를 조회한다."""
    return db.execute(select(MapFarmingItem, Item).join(Item, Item.id == MapFarmingItem.farming_item_id)
        .where(MapFarmingItem.map_id == map_id).order_by(MapFarmingItem.id)).all()
