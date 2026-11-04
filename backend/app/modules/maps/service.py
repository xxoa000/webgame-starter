"""물자·몬스터 조우를 합산한 맵별 확률과 발견 상태를 제공한다."""
from . import repository
from ..combat.repository import monster_options
from ..encyclopedia.service import known_for_user


def list_maps(db,user_id):
    """공개 맵 목록과 발견 가능한 물자 확률을 조회한다."""
    known=known_for_user(db,user_id)
    from ..items.presentation import item_traits
    traits = item_traits(db)
    result = []
    for world_map in repository.list_maps(db):
        from ..raids.service import active_event
        from ...core.config import settings
        from ..items.models import Item
        event = active_event(db, world_map.id)
        multiplier = settings.raid_monster_multiplier if event else 1
        normal_probability = .99 if event else 1
        options = repository.farming_options(db, world_map.id)
        enemies = monster_options(db, world_map.id)
        total = world_map.empty_weight + sum(link.weight for link, _ in options) + sum(link.weight for link, _ in enemies) * multiplier
        result.append({"id": world_map.id, "name": world_map.name, "description": world_map.description,
            "raid_event_id": event.id if event else None,
            "empty_probability": normal_probability * world_map.empty_weight / total,
            "monsters": [{"name": monster.name, "probability": normal_probability * link.weight * multiplier / total} for link, monster in enemies],
            "items": [{**traits[item.id], "item_id": item.id, "name": item.name if item.id in known else "???", "weight_grams": item.weight_grams if item.id in known else None, "discovered": item.id in known,
                       "probability": normal_probability * link.weight / total} for link, item in options]})
        if event:
            item = db.get(Item, event.item_id)
            result[-1]['items'].append({**traits[item.id], 'item_id': item.id, 'name': item.name,
                'weight_grams': item.weight_grams, 'discovered': item.id in known, 'probability': .01})
    return result
