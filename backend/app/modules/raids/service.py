"""전역 잠금으로 공유 HP와 단 한 번의 이벤트 정산을 처리한다."""
import secrets
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select, update
from ...core.config import settings
from ...database.base import utc_now
from ..characters.models import Character
from ..exploration.models import Exploration
from ..items.models import Item
from ..maps.models import Map
from .models import RaidCycle, RaidEvent, RaidMember

ITEM_NAME = '균열 결정'


def lock_cycle(db):
    """캐릭터 잠금보다 먼저 전역 일정을 잠가 교착과 중복 정산을 막는다."""
    dialect = db.bind.dialect.name
    if dialect == 'mysql':
        from sqlalchemy.dialects.mysql import insert
        stmt = insert(RaidCycle).values(id=1, next_at=utc_now())
        db.execute(stmt.on_duplicate_key_update(id=1))
    else:
        from sqlalchemy.dialects.sqlite import insert
        db.execute(insert(RaidCycle).values(id=1, next_at=utc_now()).on_conflict_do_nothing(index_elements=['id']))
    return db.scalar(select(RaidCycle).where(RaidCycle.id == 1).with_for_update().execution_options(populate_existing=True))


def active_event(db, map_id=None, lock=False):
    """현재 공유 균열을 읽는다. 변경 전에는 반드시 전역 잠금을 잡는다."""
    stmt = select(RaidEvent).where(RaidEvent.status != 'closed')
    if map_id is not None:
        stmt = stmt.where(RaidEvent.map_id == map_id)
    stmt = stmt.order_by(RaidEvent.id.desc()).limit(1)
    if lock:
        stmt = stmt.with_for_update().execution_options(populate_existing=True)
    return db.scalar(stmt)


def locked_event(db, event_id):
    """인증 조회가 시작한 MySQL 스냅샷 대신 잠금 후 최신 이벤트를 읽는다."""
    return db.scalar(select(RaidEvent).where(RaidEvent.id == event_id).with_for_update().execution_options(populate_existing=True))


def ensure_event(db):
    """접속 시 일정에 따라 무작위 지역 한 곳에 이벤트를 개설한다."""
    cycle = lock_cycle(db)
    event = active_event(db, lock=True)
    if event or cycle.next_at > utc_now():
        return event
    maps = list(db.scalars(select(Map).order_by(Map.id)))
    if not maps:
        return None
    item = db.scalar(select(Item).where(Item.name == ITEM_NAME).with_for_update())
    if item is None:
        item = Item(name=ITEM_NAME, description='균열 종료 시 1개당 스탯 포인트 +1로 변환된다.',
                    weight_grams=1, kind='event', is_event=True, sell_price=0, buy_price=0)
        db.add(item)
        db.flush()
    event = RaidEvent(map_id=secrets.choice(maps).id, item_id=item.id,
                      threshold=settings.raid_item_threshold, boss_hp=settings.raid_boss_hp,
                      boss_max_hp=settings.raid_boss_hp)
    db.add(event)
    db.flush()
    return event


def member_for(db, event, character):
    """한 캐릭터의 수집·공격 기록을 같은 이벤트 행에 누적한다."""
    member = db.scalar(select(RaidMember).where(RaidMember.event_id == event.id, RaidMember.character_id == character.id).with_for_update().execution_options(populate_existing=True))
    if member is None:
        member = RaidMember(event_id=event.id, character_id=character.id, name=character.name,
                            items=0, damage=0, reward=0)
        db.add(member)
        db.flush()
    return member


def collect(db, event_id, character, quantity):
    """회수한 결정을 전용 보관하고 지역 합계가 임계값에 닿으면 보스를 연다."""
    event = locked_event(db, event_id)
    if event is None or event.status == 'closed':
        return False
    member_for(db, event, character).items += quantity
    event.collected += quantity
    if event.collected >= event.threshold:
        event.status = 'boss'
    event.version += 1
    return True


def event_data(db, event, character_id=None):
    """서버 상태·개인 기여·정산 결과를 클라이언트에 공개한다."""
    if event is None:
        return None
    members = list(db.scalars(select(RaidMember).where(RaidMember.event_id == event.id).order_by(RaidMember.damage.desc(), RaidMember.id).with_for_update()))
    mine = next((m for m in members if m.character_id == character_id), None)
    return {'id': event.id, 'map_id': event.map_id, 'map_name': db.get(Map, event.map_id).name,
            'status': event.status, 'collected': event.collected, 'threshold': event.threshold,
            'boss_name': '균열의 감시자', 'boss_hp': event.boss_hp, 'boss_max_hp': event.boss_max_hp,
            'version': event.version, 'my_items': mine.items if mine else 0,
            'my_reward': mine.reward if mine else 0,
            'leaders': [{'name': m.name, 'damage': m.damage, 'reward': m.reward} for m in members if m.damage],
            'closed_at': event.closed_at.isoformat()+'Z' if event.closed_at else None}


def current(db, user_id=None):
    """일정을 갱신하고 현재 또는 가장 최근 종료 이벤트를 반환한다."""
    event = ensure_event(db)
    if event is None:
        event = db.scalar(select(RaidEvent).order_by(RaidEvent.id.desc()).limit(1).with_for_update())
    character_id = db.scalar(select(Character.id).where(Character.user_id == user_id)) if user_id else None
    result = event_data(db, event, character_id)
    db.commit()
    return result


def attack(db, user_id, event_id, version):
    """같은 지역 탐사자의 공격을 직렬화하고 실제 피해 기준으로 정산한다."""
    lock_cycle(db)
    from ..inventory.service import ready_character
    from ..characters.vitals import require_mobile
    from ..exploration.repository import get_session
    character = ready_character(db, user_id)
    require_mobile(character)
    session = get_session(db, character.id)
    event = locked_event(db, event_id)
    if not event or event.status != 'boss':
        raise HTTPException(409, '현재 공격할 수 있는 균열 보스가 없어.')
    if event.version != version:
        raise HTTPException(409, '보스 상태가 바뀌었어. 최신 상태에서 다시 공격해.')
    if not session or session.status != 'active' or session.map_id != event.map_id:
        raise HTTPException(409, '해당 이벤트 지역을 탐사 중이어야 해.')
    if session.combat or session.pending_item_id:
        raise HTTPException(409, '진행 중인 전투나 발견 물자부터 처리해.')
    damage = min(event.boss_hp, max(1, character.stats['strength'] * 2 + secrets.randbelow(4) + 1))
    member = member_for(db, event, character)
    member.damage += damage
    event.boss_hp -= damage
    event.version += 1
    from ..exploration.service import append_event
    session.turn += 1
    session.version += 1
    append_event(session, 'raid', f'균열 보스에게 {damage} 피해. 스태미나 소모 없음.')
    if event.boss_hp == 0:
        finish(db, event, member)
        append_event(session, 'raid', '보스를 처치했다. 균열 봉쇄 및 스탯 포인트 정산 완료.')
    db.flush()
    result = event_data(db, event, character.id)
    db.commit()
    return result


def finish(db, event, last_member):
    """수집·참가·최대 피해·마지막 타격 보상을 하나의 트랜잭션으로 지급한다."""
    if event.status == 'closed':
        return
    db.flush()
    members = list(db.scalars(select(RaidMember).where(RaidMember.event_id == event.id).order_by(RaidMember.id).with_for_update()))
    maximum = max((m.damage for m in members), default=0)
    for member in members:
        # 최대 피해 동률은 공동 1위로 처리한다. 참가 판정은 실제 피해 1 이상이다.
        reward = member.items + int(member.damage > 0) + (3 if maximum and member.damage == maximum else 0) + int(member.id == last_member.id)
        member.reward = reward
        if member.character_id and reward:
            db.execute(update(Character).where(Character.id == member.character_id).values(
                stat_points=Character.stat_points + reward, stat_version=Character.stat_version + 1))
    event.status, event.closed_at = 'closed', utc_now()
    db.get(RaidCycle, 1).next_at = event.closed_at + timedelta(seconds=settings.raid_cooldown_seconds)
