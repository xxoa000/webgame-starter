"""턴과 발견 아이템을 DB에 보존한다. 화면 창을 여는 동작은 서버 턴을 진행하지 않는다."""
import secrets
from fastapi import HTTPException
from ..maps.models import Map
from ..maps.repository import farming_options
from ..items.models import Item
from ..inventory.service import ready_character, ensure_inventory, add_item
from .models import Exploration
from . import repository


def append_event(session, kind, message):
    session.history = [*session.history, {"turn": session.turn, "kind": kind, "message": message}][-30:]


def state_data(db, session):
    if session is None:
        return None
    world_map = db.get(Map, session.map_id)
    pending = db.get(Item, session.pending_item_id) if session.pending_item_id else None
    return {"id": session.id, "map_id": session.map_id, "map_name": world_map.name,
            "status": session.status, "turn": session.turn, "version": session.version,
            "pending_item": {"item_id": pending.id, "name": pending.name, "description": pending.description,
                             "weight_grams": pending.weight_grams, "quantity": session.pending_quantity} if pending else None,
            "history": session.history}


def get_state(db, user_id):
    character = ready_character(db, user_id)
    return state_data(db, repository.get_session(db, character.id))


def start(db, user_id, map_id):
    character = ready_character(db, user_id)
    world_map = db.get(Map, map_id)
    if not world_map:
        raise HTTPException(404, "존재하지 않는 탐색 지역이야.")
    inventory = ensure_inventory(db, character.id)
    session = repository.get_session(db, character.id)
    if session and session.status == "active":
        if session.map_id != map_id:
            raise HTTPException(409, "진행 중인 탐색을 종료한 뒤 지역을 바꿀 수 있어.")
        db.commit()
        return state_data(db, session)
    if session is None:
        session = Exploration(character_id=character.id, map_id=map_id, status="active",
            turn=0, version=1, history=[], pending_quantity=0)
        db.add(session)
    else:
        session.map_id, session.status, session.turn = map_id, "active", 0
        session.version += 1  # Never reuse an old version after ending/restarting.
        session.pending_item_id, session.pending_quantity, session.history = None, 0, []
    append_event(session, "start", f"{world_map.name}에 들어섰다. 나무 사이로 낯선 마나가 흐른다.")
    db.commit()
    return state_data(db, session)


def draw(world_map, options):
    # Independent weighted draw on every search. Consecutive equal outcomes are possible.
    pick = secrets.randbelow(world_map.empty_weight + sum(link.weight for link, _ in options))
    if pick < world_map.empty_weight:
        return None
    pick -= world_map.empty_weight
    for link, item in options:
        if pick < link.weight:
            return item
        pick -= link.weight
    raise RuntimeError("탐색 확률 설정을 확인해.")


def act(db, user_id, body):
    character = ready_character(db, user_id)
    inventory = ensure_inventory(db, character.id)
    session = repository.get_session(db, character.id)
    if session is None or session.status != "active":
        raise HTTPException(409, "먼저 탐색을 시작해.")
    if session.id != body.exploration_id:
        raise HTTPException(409, "다른 탐색 세션이야. 현재 탐색 상태를 다시 확인해.")
    if session.version != body.version:
        raise HTTPException(409, "다른 요청에서 탐색 상태가 바뀌었어. 최신 상태를 불러왔으니 다시 선택해.")
    if session.pending_item_id is not None and body.action not in {"take", "give_up", "end"}:
        raise HTTPException(409, "발견한 아이템을 가져가거나 포기한 뒤 다음 턴을 진행해.")
    if body.action == "search":
        world_map = db.get(Map, session.map_id)
        found = draw(world_map, farming_options(db, session.map_id))
        session.turn += 1
        if found:
            session.pending_item_id, session.pending_quantity = found.id, 1
            append_event(session, "found", f"'{found.name}'을 발견했다.")
        else:
            append_event(session, "empty", "아무것도 얻지 못했다. 숲은 고요하다.")
    elif body.action == "rest":
        session.turn += 1
        append_event(session, "rest", "나무 그늘에 앉아 잠시 숨을 골랐다.")
    elif body.action in {"take", "give_up"}:
        if session.pending_item_id is None:
            raise HTTPException(409, "아직 발견한 아이템이 없어.")
        item = db.get(Item, session.pending_item_id)
        if body.action == "take":
            add_item(db, inventory, item, session.pending_quantity)
            append_event(session, "take", f"'{item.name}'을 인벤토리에 넣었다.")
        else:
            append_event(session, "give_up", f"'{item.name}'을 두고 걸음을 옮겼다.")
        session.pending_item_id, session.pending_quantity = None, 0
    elif body.action == "end":
        session.status = "ended"
        session.pending_item_id, session.pending_quantity = None, 0
        append_event(session, "end", "탐색을 마쳤다. 챙긴 아이템은 인벤토리에 남는다.")
    session.version += 1
    db.commit()
    return state_data(db, session)
