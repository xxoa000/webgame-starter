from . import repository


def list_maps(db):
    result = []
    for world_map in repository.list_maps(db):
        options = repository.farming_options(db, world_map.id)
        total = world_map.empty_weight + sum(link.weight for link, _ in options)
        result.append({"id": world_map.id, "name": world_map.name, "description": world_map.description,
            "empty_probability": world_map.empty_weight / total,
            "items": [{"item_id": item.id, "name": item.name, "weight_grams": item.weight_grams,
                       "probability": link.weight / total} for link, item in options]})
    return result
