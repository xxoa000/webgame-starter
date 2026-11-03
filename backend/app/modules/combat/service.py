"""서버에서 전투 피해·확정 도망·승리 보상·사망 보관을 처리한다."""
import secrets
from ..characters.vitals import apply_damage, limits
from ..characters.models import DeletedCharacter
from ...core.security import now
from ..encyclopedia.repository import discover
from .repository import drop_options
from .rules import INJURY_PERCENT


def enter(session, monster):
    """조우한 몬스터의 능력치와 현재 HP를 전투 상태에 저장한다."""
    session.combat = {'monster_id': monster.id, 'name': monster.name, 'description': monster.description,
        'hp': monster.hp, 'max_hp': monster.hp, 'attack_min': monster.attack_min,
        'attack_max': monster.attack_max, 'defense': monster.defense}


def die(db, character, session, log):
    # The current row becomes an immutable tombstone until a new draft replaces it.
    """사망 기록을 보관하고 캐릭터와 탐색을 종료 상태로 바꾼다."""
    from ..personality.service import snapshot
    db.add(DeletedCharacter(personality_snapshot=snapshot(character), original_character_id=character.id, user_id=character.user_id,
        name=character.name, gender=character.gender, age=character.age, bio=character.bio,
        appearance=dict(character.appearance or {}), stats=dict(character.stats), rerolls=character.rerolls,
        status='dead', deleted_at=now()))
    db.flush()
    character.status, character.name_key, character.hp_current = 'dead', None, 0
    session.status, session.combat = 'ended', None
    session.pending_item_id, session.pending_quantity = None, 0
    log(session, 'death', f'{character.name} 사망. 피계약자 연결이 종료되었다.')


def counterattack(db, character, session, log):
    """몬스터 반격 피해와 부상·사망 결과를 반영한다."""
    monster = session.combat
    damage = secrets.randbelow(monster['attack_max'] - monster['attack_min'] + 1) + monster['attack_min']
    damage = max(1, damage - character.stats['stamina'] // 4)
    apply_damage(character, damage)
    log(session, 'damage', f"{monster['name']}의 공격. HP -{damage}.")
    if character.hp_current <= 0:
        die(db, character, session, log)
    elif character.hp_current * 100 <= limits(character)[0] * INJURY_PERCENT:
        log(session, 'injury', '부상 상태. 회복이 필요하다.')


def fight(db, character, session, log):
    """한 턴의 공격과 반격 또는 승리 보상을 처리한다."""
    monster = dict(session.combat)
    damage = max(1, character.stats['strength'] * 2 + secrets.randbelow(4) + 1 - monster['defense'])
    monster['hp'] = max(0, monster['hp'] - damage)
    session.combat = monster
    log(session, 'attack', f"{monster['name']}에게 {damage} 피해를 입혔다.")
    if monster['hp']:
        counterattack(db, character, session, log)
        return
    log(session, 'victory', f"{monster['name']}을 쓰러뜨렸다.")
    session.combat = None
    drops = drop_options(db, monster['monster_id'])
    if drops and secrets.randbelow(100) < 60:
        pick = secrets.randbelow(sum(link.weight for link, _ in drops))
        for link, item in drops:
            if pick < link.weight:
                session.pending_item_id, session.pending_quantity = item.id, 1
                discover(db, character.id, item.id, session.map_id)
                log(session, 'found', f"'{item.name}'을 발견했다.")
                break
            pick -= link.weight
