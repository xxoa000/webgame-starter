"""몬스터 조우·턴 잠금·확정 도망·회복 물자·부상·사망과 재등록을 검증한다."""
import pytest
from sqlalchemy import select, func
from test_flow import client
from test_exploration import world, start, act
from app.modules.characters.models import Character, DeletedCharacter
from app.modules.monsters.models import Monster
from app.modules.maps.models import MapMonster
from app.modules.items.models import Item
from app.modules.inventory.models import Inventory, InventoryEntry
from app.modules.exploration.models import Exploration


@pytest.fixture
def battlefield(world, monkeypatch):
    """테스트에 필요한 데이터와 검증 조건을 준비한다."""
    c, factory, character = world
    with factory() as db:
        monster = Monster(name='테스트 감염체', description='시험 개체', hp=100, attack_min=8, attack_max=8, defense=0)
        db.add(monster); db.flush()
        db.add(MapMonster(map_id=1, monster_id=monster.id, weight=100))
        bandage = Item(name='멸균 붕대', description='회복 물자', weight_grams=80, kind='farming')
        db.add(bandage); db.flush()
        inventory = db.scalar(select(Inventory).where(Inventory.character_id == character['id']))
        db.add(InventoryEntry(inventory_id=inventory.id, item_id=bandage.id, quantity=2))
        db.commit(); item_id = bandage.id
    monkeypatch.setattr('app.modules.exploration.service.secrets.randbelow', lambda size: 0)
    state = act(c, start(c), 'search').json()
    assert state['combat']['name'] == '테스트 감염체'
    return c, factory, character, state, item_id


def test_flee_is_guaranteed_and_persistent(battlefield):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, _, _, state, _ = battlefield
    assert c.get('/exploration/state').json()['combat'] == state['combat']
    hp = state['vitals']['hp_current']
    for action in ['rest', 'search', 'end', 'take']:
        assert act(c, state, action).status_code == 409
    escaped = act(c, state, 'flee')
    assert escaped.status_code == 200
    escaped = escaped.json()
    assert escaped['combat'] is None and escaped['vitals']['hp_current'] == hp
    assert escaped['status'] == 'active'
    assert act(c, state, 'fight').status_code == 409
    assert act(c, escaped, 'fight').status_code == 409


def test_injury_and_item_consumption(battlefield):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory, character, state, item_id = battlefield
    with factory() as db:
        db.get(Character, character['id']).hp_current = 13
        db.commit()
    injured = act(c, state, 'fight').json()
    assert injured['vitals']['hp_current'] == 6
    assert injured['vitals']['condition'] == '부상'
    assert c.get('/characters/vitals').json()['condition'] == '부상'
    assert act(c, injured, 'use_item', item_id=999999).status_code == 409
    healed = act(c, injured, 'use_item', item_id=item_id).json()
    assert healed['vitals']['hp_current'] == 9  # +10 then enemy -7
    assert healed['vitals']['stamina_current'] == injured['vitals']['stamina_current']
    assert c.get('/inventory').json()['items'][0]['quantity'] == 1
    assert act(c, injured, 'use_item', item_id=item_id).status_code == 409
    escaped = act(c, healed, 'flee').json()
    restored = act(c, escaped, 'use_item', item_id=item_id).json()
    assert restored['vitals']['hp_current'] == 19 and restored['vitals']['condition'] == '정상'
    assert not c.get('/inventory').json()['items']
    rested = act(c, restored, 'rest').json()
    assert rested['vitals']['hp_current'] == 21


def test_death_is_archived_once_and_new_character_possible(battlefield):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory, character, state, item_id = battlefield
    with factory() as db:
        db.get(Character, character['id']).hp_current = 1
        db.commit()
    dead = act(c, state, 'fight').json()
    assert dead['dead'] and dead['status'] == 'ended' and dead['combat'] is None
    assert dead['vitals']['hp_current'] == 0 and dead['vitals']['condition'] == '사망'
    for action in ['rest', 'use_item', 'fight', 'flee', 'search']:
        assert act(c, dead, action, item_id=item_id).status_code == 409
    assert c.post('/exploration/start', json={'map_id': 1}).status_code == 409
    assert c.get('/me').json()['character']['status'] == 'dead'
    with factory() as db:
        records = db.scalars(select(DeletedCharacter)).all()
        assert len(records) == 1 and records[0].status == 'dead'
        assert records[0].user_id == db.get(Character, character['id']).user_id
    assert c.get('/characters/check-name', params={'name': character['name']}).json()['available']
    draft = c.post('/characters/draft', json={})
    assert draft.status_code == 200 and draft.json()['status'] == 'draft'
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Exploration)) == 0
        assert db.scalar(select(func.count()).select_from(InventoryEntry)) == 0
        assert db.scalar(select(func.count()).select_from(DeletedCharacter)) == 1


def test_victory_prevents_counterattack(battlefield):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory, _, state, _ = battlefield
    with factory() as db:
        session = db.get(Exploration, state['id'])
        session.combat = {**session.combat, 'hp': 1}
        db.commit()
    won = act(c, state, 'fight').json()
    assert won['combat'] is None
    assert won['vitals']['hp_current'] == state['vitals']['hp_current']
    assert any(event['kind'] == 'victory' for event in won['history'])


def test_world_combat_migration_replays_without_duplicates(tmp_path):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    import importlib.util
    from pathlib import Path
    import sqlalchemy as sa
    from alembic import command
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    from test_alembic import config_for
    engine = sa.create_engine('sqlite:///' + str(tmp_path/'combat.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db), '0007_apocalypse_world')
    with engine.begin() as db:
        # Simulate MySQL having retained a column after an interrupted DDL migration.
        db.execute(sa.text('ALTER TABLE monster ADD COLUMN hp INTEGER NOT NULL DEFAULT 20'))
    with engine.connect() as db:
        command.upgrade(config_for(db), 'head')
    with engine.begin() as db:
        spec = importlib.util.spec_from_file_location('combat_revision', Path(__file__).resolve().parents[1]/'alembic/versions/0008_combat.py')
        revision = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(revision)
        with Operations.context(MigrationContext.configure(db)):
            revision.upgrade()
        for table, count in [('map', 8), ('monster', 8), ('map_monster', 8), ('item', 32), ('monster_drop_item', 8)]:
            assert db.execute(sa.text(f'SELECT COUNT(*) FROM {table}')).scalar_one() == count
        assert db.execute(sa.text('SELECT COUNT(*) FROM monster WHERE hp <= 0 OR attack_min < 1 OR attack_max < attack_min OR defense < 0')).scalar_one() == 0
    engine.dispose()
