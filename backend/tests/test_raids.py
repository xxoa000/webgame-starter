"""공유 보스·발견 확률·권한·중복 공격·일회성 보상 정산을 검증한다."""
from datetime import timedelta
from sqlalchemy import select
from test_flow import client, make_ready
from test_exploration import world, start, act
from app.core.config import settings
from app.database.base import utc_now
from app.modules.raids.models import RaidCycle, RaidEvent, RaidMember
from app.modules.characters.models import Character
from app.modules.exploration.models import Exploration
from app.modules.raids import service
from app.modules.maps.models import MapMonster
from app.modules.monsters.models import Monster


def event_for(c, monkeypatch, threshold=1, hp=100):
    """대상 지역과 보스 등장 조건을 고정한다."""
    monkeypatch.setattr(settings, 'raid_item_threshold', threshold)
    monkeypatch.setattr(settings, 'raid_boss_hp', hp)
    monkeypatch.setattr(service.secrets, 'choice', lambda maps: maps[0])
    response = c.get('/raids/mine')
    assert response.status_code == 200
    return response.json()


def collect_one(c, state, monkeypatch):
    """1% 발견 분기부터 회수까지 실제 API로 실행한다."""
    monkeypatch.setattr('app.modules.exploration.service.secrets.randbelow', lambda n: 0)
    found = act(c, state, 'search').json()
    assert found['pending_item']['rarity'] == 'mythic'
    assert found['pending_item']['name'] == '균열 결정'
    response = act(c, found, 'take')
    assert response.status_code == 200, response.text
    assert act(c, found, 'take').status_code == 409
    return response.json()


def test_shared_boss_rewards_and_no_stamina(world, monkeypatch):
    """두 사람의 수집·참가·최대 피해·마지막 타격을 중첩해 한 번만 지급한다."""
    c, factory, character = world
    event = event_for(c, monkeypatch, hp=20)
    state = collect_one(c, start(c, event['map_id']), monkeypatch)
    assert c.get('/inventory').json()['items'] == []
    boss = c.get('/raids/mine').json()
    assert boss['status'] == 'boss' and boss['my_items'] == 1
    first = c.post(f"/raids/{event['id']}/attack", json={'version': boss['version']})
    assert first.status_code == 200, first.text
    first = first.json()
    assert first['boss_hp'] == 11  # strength=4 => 9 damage
    assert c.post(f"/raids/{event['id']}/attack", json={'version': boss['version']}).status_code == 409
    assert c.get('/exploration/state').json()['vitals']['stamina_current'] == state['vitals']['stamina_current']
    c.post('/auth/logout', json={})
    creds = {'username': 'raid_second', 'password': 'test-password-123'}
    assert c.post('/auth/signup', json=creds).status_code == 201
    assert c.post('/auth/login', json=creds).status_code == 200
    second = make_ready(c, '레이드둘')
    with factory() as db:
        other = db.get(Character, second['id'])
        other.stats = {**other.stats, 'strength': 20}
        db.commit()
    start(c, event['map_id'])
    killed = c.post(f"/raids/{event['id']}/attack", json={'version': first['version']})
    assert killed.status_code == 200, killed.text
    killed = killed.json()
    assert killed['boss_hp'] == 0 and killed['status'] == 'closed'
    assert killed['my_reward'] == 5  # actual damage 11: participant+MVP+last
    with factory() as db:
        assert db.get(Character, character['id']).stat_points == 2  # item+participant
        assert db.get(Character, second['id']).stat_points == 5
        assert sorted(m.damage for m in db.scalars(select(RaidMember))) == [9, 11]
    assert c.post(f"/raids/{event['id']}/attack", json={'version': killed['version']}).status_code == 409
    for _ in range(2):
        assert c.get('/raids/mine').json()['status'] == 'closed'
    assert c.get('/me').json()['character']['stat_points'] == 5


def test_event_only_probability_and_collection_gate(world, monkeypatch):
    """대상 지역만 확률을 바꾸고 회수할 때 보스 등장 조건을 진행한다."""
    c, factory, _ = world
    with factory() as db:
        monster = Monster(name='확률 검증 몬스터', description='이벤트 조우 배율 검증')
        db.add(monster)
        db.flush()
        db.add(MapMonster(map_id=1, monster_id=monster.id, weight=20))
        db.commit()
    before = c.get('/maps').json()
    event = event_for(c, monkeypatch, threshold=2)
    maps = c.get('/maps').json()
    selected = next(m for m in maps if m['id'] == event['map_id'])
    assert selected['items'][-1]['probability'] == .01
    assert selected['items'][-1]['rarity'] == 'mythic'
    assert selected['raid_event_id'] == event['id']
    assert selected['monsters'][0]['probability'] > before[0]['monsters'][0]['probability']
    assert abs(selected['empty_probability'] + sum(i['probability'] for i in selected['items']) + sum(m['probability'] for m in selected['monsters']) - 1) < 1e-9
    assert maps[1]['items'] == before[1]['items']
    state = start(c, event['map_id'])
    monkeypatch.setattr(service.secrets, 'randbelow', lambda n: 0)
    found = act(c, state, 'search').json()
    assert c.get('/raids/mine').json()['collected'] == 0
    state = act(c, found, 'give_up').json()
    state = collect_one(c, state, monkeypatch)
    assert c.get('/raids/mine').json()['status'] == 'collecting'
    collect_one(c, state, monkeypatch)
    assert c.get('/raids/mine').json()['status'] == 'boss'
    with factory() as db:
        assert len(list(db.scalars(select(RaidEvent)))) == 1


def test_collectors_and_joint_mvp_rewards_are_settled_once(world, monkeypatch):
    """공격하지 않은 수집자도 결정을 변환하고 최대 피해 동률자는 공동 보상한다."""
    from app.modules.users.models import User
    c, factory, character = world
    event = event_for(c, monkeypatch)
    with factory() as db:
        service.lock_cycle(db)
        stored = db.get(RaidEvent, event['id'])
        first = db.get(Character, character['id'])
        first_member = service.member_for(db, stored, first)
        first_member.items, first_member.damage = 1, 9
        others = []
        for index in range(2):
            user = User(username=f'reward_member_{index}', password_hash='not-a-login-account')
            db.add(user)
            db.flush()
            other = Character(user_id=user.id, name=f'참가{index}', stats=dict(first.stats), status='ready')
            db.add(other)
            db.flush()
            others.append(other)
        last = service.member_for(db, stored, others[0])
        last.damage = 9
        collector = service.member_for(db, stored, others[1])
        collector.items = 2
        stored.boss_hp = 0
        service.finish(db, stored, last)
        db.commit()
        assert [db.get(Character, row.id).stat_points for row in [first, *others]] == [5, 5, 2]
        service.finish(db, stored, last)
        db.commit()
        assert [db.get(Character, row.id).stat_points for row in [first, *others]] == [5, 5, 2]


def test_attack_requires_map_mobile_clear_encounter_and_fresh_version(world, monkeypatch):
    """다른 지역·일반 전투·빈사·미인증 상태의 공격을 거절한다."""
    c, factory, character = world
    event = event_for(c, monkeypatch)
    with factory() as db:
        db.get(RaidEvent, event['id']).status = 'boss'
        db.commit()
    attack = lambda: c.post(f"/raids/{event['id']}/attack", json={'version': event['version']})
    assert attack().status_code == 409
    start(c, event['map_id'])
    with factory() as db:
        session = db.scalar(select(Exploration))
        session.combat = {'name': '위협'}
        db.commit()
    assert attack().status_code == 409
    with factory() as db:
        db.scalar(select(Exploration)).combat = None
        db.get(Character, character['id']).downed = True
        db.commit()
    assert attack().status_code == 409
    c.post('/auth/logout', json={})
    assert attack().status_code == 401


def test_cooldown_and_pending_old_event_cannot_credit_new_event(world, monkeypatch):
    """닫힌 이벤트의 미회수 물자를 다음 이벤트로 넘기지 않는다."""
    c, factory, _ = world
    event = event_for(c, monkeypatch)
    state = start(c, event['map_id'])
    monkeypatch.setattr(service.secrets, 'randbelow', lambda n: 0)
    found = act(c, state, 'search').json()
    with factory() as db:
        db.get(RaidEvent, event['id']).status = 'closed'
        db.get(RaidCycle, 1).next_at = utc_now() + timedelta(hours=1)
        db.commit()
    assert c.get('/raids/mine').json()['id'] == event['id']
    with factory() as db:
        db.get(RaidCycle, 1).next_at = utc_now() - timedelta(seconds=1)
        db.commit()
    next_event = c.get('/raids/mine').json()
    assert next_event['id'] != event['id']
    assert act(c, found, 'take').status_code == 200
    assert c.get('/raids/mine').json()['collected'] == 0
