"""턴과 발견 아이템을 DB에 보존한다. 화면 창을 여는 동작은 서버 턴을 진행하지 않는다."""
import secrets
from uuid import uuid4
from sqlalchemy.orm import object_session
from fastapi import HTTPException
from ..maps.models import Map
from ..maps.repository import farming_options
from ..items.models import Item
from ..inventory.service import ready_character, ensure_inventory, add_item
from .models import Exploration
from ..characters.vitals import data as vitals_data, spend_stamina, recover
from ..characters.models import Character
from ..characters.rules import REST_MIN_PERCENT, REST_MAX_PERCENT
from ..encyclopedia.repository import discover
from . import repository
from ..rescue.service import rescue_data, resolve_due
from ..combat import service as combat_service
from ..combat.repository import monster_options
from ..combat.items import use_item


def append_event(session, kind, message):
    """최근 탐색 기록에 턴 결과를 추가한다."""
    outputs = []
    db = object_session(session)
    if db is not None:
        from ..scripts.service import select_output
        character = db.get(Character, session.character_id)
        world_map = db.get(Map, session.map_id)
        item = db.get(Item, session.pending_item_id) if session.pending_item_id else None
        context = {'character_name':character.name, 'map_name':world_map.name,
            'item_name':item.name if item else '물자', 'monster_name':(session.combat or {}).get('name','위협 개체')}
        outputs = select_output(db, character, kind, session.map_id, context, session.history, action=getattr(session, "_script_action", None))
    session.history = [*session.history, {"event_key":uuid4().hex,"turn":session.turn,"kind":kind,"message":message,"scripts":outputs}][-30:]


def state_data(db, session):
    """탐색 세션과 발견 물자·전투·자원을 응답으로 구성한다."""
    if session is None:
        return None
    world_map = db.get(Map, session.map_id)
    pending = db.get(Item, session.pending_item_id) if session.pending_item_id else None
    from ..items.presentation import item_traits
    traits = item_traits(db) if pending else {}
    if pending and session.pending_raid_id:
        traits[pending.id] = {'rarity': 'mythic', 'edible': False}
    return {"id": session.id, "map_id": session.map_id, "map_name": world_map.name,
            "downed": db.get(Character,session.character_id).downed, "rescue": rescue_data(db, session.character_id), "position_step": session.position_step, "status": session.status, "turn": session.turn, "version": session.version,
            "pending_item": {**traits[pending.id], "item_id": pending.id, "name": pending.name, "description": pending.description,
                             "weight_grams": pending.weight_grams, "quantity": session.pending_quantity} if pending else None,
            "combat": session.combat, "dead": db.get(Character,session.character_id).status == "dead",
            "history": [{**event, "scripts": [{key:value for key,value in output.items() if key != "visibility"} for output in event.get("scripts", [])]} for event in session.history], "vitals": vitals_data(db.get(Character,session.character_id))}


def get_state(db, user_id):
    """현재 캐릭터의 탐색 상태를 조회한다."""
    from ..characters.repository import lock_owned
    character=lock_owned(db,user_id)
    if not character or character.status not in {'ready','dead'}:
        raise HTTPException(409,'조회할 피계약자가 없어.')
    if character.status=='ready':
        from ..characters.vitals import sync
        sync(character)
    resolve_due(db, character)
    result=state_data(db, repository.get_session(db, character.id))
    db.commit()
    return result


def start(db, user_id, map_id):
    """맵을 확인하고 탐색을 시작하거나 기존 상태를 반환한다."""
    character = ready_character(db, user_id)
    from ..characters.vitals import require_mobile
    require_mobile(character)
    if len(character.personality) != 3:
        raise HTTPException(409, '캐릭터 메뉴에서 성격을 먼저 선택해.')
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
        session.pending_raid_id = None
        session.position_step = 0
    append_event(session, "start", f"{world_map.name}에 들어섰다. 원격 관측 연결을 확인했다.")
    db.commit()
    return state_data(db, session)


def draw(world_map, options):
    # Independent weighted draw on every search. Consecutive equal outcomes are possible.
    """지역별 가중치에 따라 탐색 결과를 추첨한다."""
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
    """턴 버전과 선택지를 검사하고 탐색 행동을 실행한다."""
    from ..raids import service as raids
    raids.lock_cycle(db)
    character = ready_character(db, user_id)
    from ..characters.vitals import require_mobile
    require_mobile(character)
    if len(character.personality) != 3:
        raise HTTPException(409, '캐릭터 메뉴에서 성격을 먼저 선택해.')
    inventory = ensure_inventory(db, character.id)
    session = repository.get_session(db, character.id)
    if session is None or session.status != "active":
        raise HTTPException(409, "먼저 탐색을 시작해.")
    if session.id != body.exploration_id:
        raise HTTPException(409, "다른 탐색 세션이야. 현재 탐색 상태를 다시 확인해.")
    if session.version != body.version:
        raise HTTPException(409, "다른 요청에서 탐색 상태가 바뀌었어. 최신 상태를 불러왔으니 다시 선택해.")
    session._script_action = body.action
    if session.combat:
        if body.action not in {'fight', 'flee', 'use_item'}:
            raise HTTPException(409, '몬스터와 대치 중이야. 전투·도망·아이템을 선택해.')
        if body.action != 'use_item':
            session.turn += 1
        if body.action == 'flee':
            session.combat = None
            append_event(session, 'flee', '도망에 성공했다. 안전 거리를 확보했다.')
        elif body.action == 'fight':
            combat_service.fight(db, character, session, append_event)
        else:
            if body.item_id is None:
                raise HTTPException(422, '사용할 아이템을 선택해.')
            append_event(session, 'item', use_item(db, character, inventory, body.item_id))
        session.version += 1
        db.commit()
        return state_data(db, session)
    if body.action in {'fight', 'flee'}:
        raise HTTPException(409, '현재 대치 중인 몬스터가 없어.')
    if session.pending_item_id is not None and body.action not in {"take", "give_up", "end"}:
        raise HTTPException(409, "발견한 아이템을 가져가거나 포기한 뒤 다음 턴을 진행해.")
    if body.action == "search":
        spend_stamina(character)
        session.position_step += 1
        world_map = db.get(Map, session.map_id)
        options = farming_options(db, session.map_id)
        enemies = monster_options(db, session.map_id)
        event = raids.active_event(db, session.map_id, lock=True)
        multiplier = raids.settings.raid_monster_multiplier if event else 1
        monster_weight = sum(link.weight for link, _ in enemies) * multiplier
        base_weight = world_map.empty_weight + sum(link.weight for link, _ in options)
        # 매 탐색마다 독립 1% 추첨: 다른 가중치가 이벤트 물자 확률을 희석하지 않는다.
        if event and secrets.randbelow(100) == 0:
            session.turn += 1
            session.pending_item_id, session.pending_quantity = event.item_id, 1
            session.pending_raid_id = event.id
            discover(db, character.id, event.item_id, session.map_id)
            append_event(session, 'found', "'균열 결정'을 발견했다. 회수하면 균열 전용 보관함에 저장된다.")
            session.version += 1
            db.commit()
            return state_data(db, session)
        encounter = secrets.randbelow(base_weight + monster_weight) if enemies else monster_weight
        session.turn += 1
        if encounter < monster_weight:
            for link, monster in enemies:
                if encounter < link.weight * multiplier:
                    combat_service.enter(session, monster)
                    append_event(session, 'encounter', f'{monster.name} 출현.')
                    break
                encounter -= link.weight * multiplier
            session.version += 1
            db.commit()
            return state_data(db, session)
        found = draw(world_map, options)
        if found:
            discover(db,character.id,found.id,session.map_id)
            session.pending_item_id, session.pending_quantity = found.id, 1
            append_event(session, "found", f"'{found.name}'을 발견했다.")
        else:
            append_event(session, "empty", "아무것도 얻지 못했다. 추가 이상 징후 없음.")
    elif body.action == 'use_item':
        if body.item_id is None:
            raise HTTPException(422, '사용할 아이템을 선택해.')
        append_event(session, 'item', use_item(db, character, inventory, body.item_id))
    elif body.action == "rest":
        spend_stamina(character)
        session.turn += 1
        hp_gain,mp_gain=recover(character,secrets.randbelow(REST_MAX_PERCENT-REST_MIN_PERCENT+1)+REST_MIN_PERCENT,secrets.randbelow(REST_MAX_PERCENT-REST_MIN_PERCENT+1)+REST_MIN_PERCENT)
        append_event(session, "rest", f"숨을 골랐다. HP +{hp_gain}, MP +{mp_gain}.")
    elif body.action in {"take", "give_up"}:
        if session.pending_item_id is None:
            raise HTTPException(409, "아직 발견한 아이템이 없어.")
        item = db.get(Item, session.pending_item_id)
        if body.action == "take":
            if session.pending_raid_id:
                collected = raids.collect(db, session.pending_raid_id, character, session.pending_quantity)
                append_event(session, 'take', '균열 결정을 전용 보관함에 회수했다.' if collected else '이미 닫힌 균열의 결정이 소멸했다.')
            else:
                add_item(db, inventory, item, session.pending_quantity)
                append_event(session, "take", f"'{item.name}'을 인벤토리에 넣었다.")
        else:
            append_event(session, "give_up", f"'{item.name}'을 두고 걸음을 옮겼다.")
        session.pending_item_id, session.pending_quantity = None, 0
        session.pending_raid_id = None
    elif body.action == "end":
        session.status = "ended"
        session.pending_item_id, session.pending_quantity = None, 0
        session.pending_raid_id = None
        append_event(session, "end", "탐색을 마쳤다. 회수한 아이템은 인벤토리에 남는다.")
    session.version += 1
    db.commit()
    return state_data(db, session)
