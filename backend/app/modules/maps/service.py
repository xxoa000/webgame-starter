"""물자·몬스터 조우를 합산한 맵별 확률과 발견 상태를 제공한다."""
from . import repository
from ..combat.repository import monster_options
from ..encyclopedia.service import known_for_user


def list_maps(db,user_id):
    """공개 맵 목록과 발견 가능한 물자 확률을 조회한다."""
    known=known_for_user(db,user_id)
    result = []
    for world_map in repository.list_maps(db):
        options = repository.farming_options(db, world_map.id)
        enemies = monster_options(db, world_map.id)
        total = world_map.empty_weight + sum(link.weight for link, _ in options) + sum(link.weight for link, _ in enemies)
        result.append({"id": world_map.id, "name": world_map.name, "description": world_map.description,
            "empty_probability": world_map.empty_weight / total,
            "monsters": [{"name": monster.name, "probability": link.weight / total} for link, monster in enemies],
            "items": [{"item_id": item.id, "name": item.name if item.id in known else "???", "weight_grams": item.weight_grams if item.id in known else None, "discovered": item.id in known,
                       "probability": link.weight / total} for link, item in options]})
    return result
