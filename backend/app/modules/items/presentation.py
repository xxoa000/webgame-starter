""" DB 가중치로 아이템 등급을 계산하고 식음료 표시 정보를 한 번에 만든다. """

from collections import defaultdict
from sqlalchemy import select
from .models import Item
from ..maps.models import Map, MapFarmingItem, MapMonster
from ..monsters.models import MonsterDropItem


def rarity_for(probability, is_event=False):
    """ 좁은 확률 구간부터 판정하며 Mythic은 이벤트 물품에만 부여한다. 
        probability: 확률을 0~1 사이로 계산한 값. (.01 = 1% / 1 = 100%)
    """

    if probability is None:
        return 'Common'

    # is_event 로 이벤트 아이템 유무를 확인, 1e-12는 아주 작은 값으로 무한 소수점을 예방하기 위함.
    if is_event and probability <= .01 + 1e-12:
        return 'Mythic'

    # limit: 확률 기준, grade: 등급 이름
    for limit, grade in (
        (.03, 'Legendary'),
        (.07, 'Epic'),
        (.15, 'Rare'),
        (.30, 'Uncommon')
    ):
        if probability <= limit + 1e-12:
            return grade

    return 'Common'


# traits : 특성, 특징, 성질
def item_traits(db):
    """ 여러 출처는 가장 높은 탐색당 확률을 사용해 동일 아이템의 등급을 일관되게 표시한다. """

    totals = {row.id: row.empty_weight for row in db.scalars(select(Map))}
    farms = db.scalars(select(MapFarmingItem)).all()
    enemies = db.scalars(select(MapMonster)).all()
    drops = db.scalars(select(MonsterDropItem)).all()
    drop_totals = defaultdict(int)

    for row in farms:
        totals[row.map_id] += row.weight
    for row in enemies:
        totals[row.map_id] += row.weight
    for row in drops:
        drop_totals[row.monster_id] += row.weight

    probabilities = defaultdict(list)

    for row in farms:
        probabilities[row.farming_item_id].append(row.weight / totals[row.map_id])
    by_monster = defaultdict(list)
    for row in drops:
        by_monster[row.monster_id].append(row)
    for enemy in enemies:
        for drop in by_monster[enemy.monster_id]:
            probabilities[drop.drop_item_id].append(
                enemy.weight / totals[enemy.map_id] * .6 * drop.weight / drop_totals[enemy.monster_id]
            )
    result = {}

    for item in db.scalars(select(Item)):
        chance = max(probabilities[item.id]) if probabilities[item.id] else None
        result[item.id] = {'rarity': rarity_for(chance, item.is_event), 'edible': bool(item.edible)}
        
    return result
