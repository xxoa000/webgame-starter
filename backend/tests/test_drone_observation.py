"""탐색 지도 위치 보존과 온라인 접속 집계를 검증한다."""
from datetime import timedelta
import sqlalchemy as sa
from test_exploration import world, start, act
from test_flow import client
from app.database.base import utc_now
from app.modules.exploration.models import ExplorationPresence
from app.modules.characters.models import Character


def test_position_only_moves_on_search(world, monkeypatch):
    """탐색 때만 이동하고 조회·휴식은 위치를 유지한다."""
    c, _, _ = world
    monkeypatch.setattr('app.modules.exploration.service.secrets.randbelow', lambda n: 0)
    state = start(c)
    assert state['position_step'] == 0
    state = act(c, state, 'search').json()
    assert state['position_step'] == 1
    assert c.get('/exploration/state').json()['position_step'] == 1
    state = act(c, state, 'rest').json()
    assert state['position_step'] == 1
    act(c, state, 'end')
    assert start(c)['position_step'] == 0


def test_presence_distinct_ttl_and_end(world):
    """계정당 한 명이며 만료·종료·사망한 탐색은 제외한다."""
    c, factory, character = world
    state = start(c)
    assert c.get('/exploration/presence').json()['counts'] == {}
    for _ in range(2):
        assert c.post('/exploration/presence', json={}).json()['counts'] == {'1': 1}
    with factory() as db:
        rows = db.scalars(sa.select(ExplorationPresence)).all()
        assert len(rows) == 1
        rows[0].last_seen_at = utc_now() - timedelta(seconds=91)
        db.commit()
    assert c.get('/exploration/presence').json()['counts'] == {}
    c.post('/exploration/presence', json={})
    assert act(c, state, 'end').status_code == 200
    assert c.get('/exploration/presence').json()['counts'] == {}
    start(c)
    c.post('/exploration/presence', json={})
    with factory() as db:
        db.get(Character, character['id']).status = 'dead'
        db.commit()
    assert c.get('/exploration/presence').json()['counts'] == {}


def test_presence_requires_auth(client):
    """인증되지 않은 사용자의 집계 조회·갱신을 차단한다."""
    c, _ = client
    assert c.get('/exploration/presence').status_code == 401
    assert c.post('/exploration/presence', json={}).status_code == 401


def test_drone_migration_preserves_turn(tmp_path):
    """위치 필드 추가와 되돌리기 모두 기존 탐색 턴을 보존한다."""
    import importlib.util
    from pathlib import Path
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    spec = importlib.util.spec_from_file_location('drone_revision', Path(__file__).resolve().parents[1] / 'alembic/versions/0014_drone_observation.py')
    revision = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(revision)
    engine = sa.create_engine('sqlite:///' + str(tmp_path / 'drone.db'))
    with engine.begin() as db:
        db.exec_driver_sql('CREATE TABLE users (id INTEGER PRIMARY KEY)')
        db.exec_driver_sql('CREATE TABLE map (id INTEGER PRIMARY KEY)')
        db.exec_driver_sql('CREATE TABLE exploration (id INTEGER PRIMARY KEY, turn INTEGER)')
        db.exec_driver_sql('INSERT INTO exploration VALUES (1,49)')
        with Operations.context(MigrationContext.configure(db)):
            revision.upgrade()
        assert db.exec_driver_sql('SELECT turn,position_step FROM exploration').one() == (49,0)
        assert 'exploration_presence' in sa.inspect(db).get_table_names()
        with Operations.context(MigrationContext.configure(db)):
            revision.downgrade()
        assert db.exec_driver_sql('SELECT turn FROM exploration').scalar_one() == 49
    engine.dispose()
