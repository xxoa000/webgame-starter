"""HP=체력×10, MP=지능×10, 스태미나=민첩. 시간 회복은 서버 UTC 기준."""
import math
from datetime import timedelta
from ...core.security import now

from .rules import HP_PER_STAMINA, MP_PER_INTELLIGENCE, STAMINA_INTERVAL_SECONDS


def limits(character):
    """능력치에 따른 자원 최대치를 계산한다."""
    return character.stats['stamina'] * HP_PER_STAMINA, character.stats['intelligence'] * MP_PER_INTELLIGENCE, character.stats['agility']


def initialize(character):
    """캐릭터 자원을 최대치로 초기화한다."""
    character.hp_current, character.mp_current, character.stamina_current = limits(character)
    character.stamina_updated_at = now()


def sync(character):
    """자원 상한과 경과 시간에 따른 스태미나 회복을 반영한다."""
    hp, mp, maximum = limits(character)
    current_time = now()
    character.hp_current = min(hp, max(0, character.hp_current if character.hp_current is not None else hp))
    character.mp_current = min(mp, max(0, character.mp_current if character.mp_current is not None else mp))
    character.stamina_current = min(maximum, max(0, character.stamina_current if character.stamina_current is not None else maximum))
    anchor = character.stamina_updated_at or current_time
    if character.stamina_current >= maximum:
        character.stamina_updated_at = current_time
        return
    elapsed = max(0, (current_time - anchor).total_seconds())
    ticks = int(elapsed // STAMINA_INTERVAL_SECONDS)
    character.stamina_current = min(maximum, character.stamina_current + ticks)
    character.stamina_updated_at = (current_time if character.stamina_current == maximum
        else anchor + timedelta(seconds=ticks * STAMINA_INTERVAL_SECONDS))


def spend_stamina(character):
    """행동 가능 여부를 검사하고 탐색 스태미나를 소비한다."""
    from fastapi import HTTPException
    sync(character)
    if character.status == 'dead' or character.hp_current == 0:
        raise HTTPException(409, '사망한 피계약자는 행동할 수 없어.')
    if character.stamina_current < 1:
        raise HTTPException(409, '스태미나가 부족해. 5분마다 1씩 자연 회복돼.')
    if character.stamina_current == limits(character)[2]:
        character.stamina_updated_at = now()
    character.stamina_current -= 1


def recover(character, hp_percent, mp_percent):
    """지정한 최대치 비율만큼 HP와 MP를 회복한다."""
    if character.status == 'dead' or character.hp_current == 0:
        from fastapi import HTTPException
        raise HTTPException(409, '사망한 피계약자는 회복할 수 없어.')
    sync(character)
    hp, mp, _ = limits(character)
    hp_before, mp_before = character.hp_current, character.mp_current
    character.hp_current = min(hp, hp_before + math.ceil(hp * hp_percent / 100))
    character.mp_current = min(mp, mp_before + math.ceil(mp * mp_percent / 100))
    return character.hp_current - hp_before, character.mp_current - mp_before


def data(character):
    """현재 자원과 다음 회복 시각을 응답 형식으로 구성한다."""
    if character.status not in {'ready', 'dead'}:
        return None
    hp, mp, maximum = limits(character)
    current_time = now()
    current = min(maximum, max(0, character.stamina_current or 0))
    missing = maximum - current
    elapsed = max(0, (current_time - (character.stamina_updated_at or current_time)).total_seconds())
    next_seconds = max(0, math.ceil(STAMINA_INTERVAL_SECONDS - elapsed)) if missing else 0
    return {'condition': '사망' if character.status == 'dead' else '부상' if (character.hp_current or 0) * 100 <= hp * 30 else '정상', 'hp_current': min(hp,max(0,character.hp_current or 0)), 'hp_max': hp,
            'hp_percent': round(min(hp,max(0,character.hp_current or 0))/hp*100,2),
            'mp_current': min(mp,max(0,character.mp_current or 0)), 'mp_max': mp,
            'mp_percent': round(min(mp,max(0,character.mp_current or 0))/mp*100,2),
            'stamina_current': current, 'stamina_max': maximum,
            'next_stamina_seconds': next_seconds,
            'full_stamina_seconds': next_seconds + max(0,missing-1)*STAMINA_INTERVAL_SECONDS if missing else 0,
            'server_time': current_time.isoformat()+'Z'}


def apply_damage(character, hp_amount=0, mp_amount=0):
    """향후 이벤트·마법 사용에서 호출. 클라이언트에게 임의 변경 API는 노출하지 않는다."""
    sync(character)
    character.hp_current=max(0,character.hp_current-max(0,int(hp_amount)))
    character.mp_current=max(0,character.mp_current-max(0,int(mp_amount)))


def restore_points(character, hp_amount=0, mp_amount=0):
    """향후 아이템 효과에서 호출. 최대치 초과 회복과 스태미나 회복은 하지 않는다."""
    if character.status == 'dead' or character.hp_current == 0:
        from fastapi import HTTPException
        raise HTTPException(409, '사망한 피계약자는 회복할 수 없어.')
    sync(character)
    hp,mp,_=limits(character)
    character.hp_current=min(hp,character.hp_current+max(0,int(hp_amount)))
    character.mp_current=min(mp,character.mp_current+max(0,int(mp_amount)))
