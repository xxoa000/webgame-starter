"""현재 마이그레이션까지 기존 데이터와 기능이 보존되는지 검증한다."""
from datetime import datetime, timedelta
import pytest
import sqlalchemy as sa
from alembic import command
from test_exploration import world, client, start, act, force_draw, core_state
from test_flow import auth, CREDS, make_ready
from test_alembic import config_for, insert_data, head
from app.modules.characters.models import Character
from app.modules.characters import vitals
from app.modules.encyclopedia.models import Encyclopedia


@pytest.fixture
def clock(monkeypatch):
    """테스트에 필요한 데이터와 검증 조건을 준비한다."""
    current=[datetime(2026,11,3,0,0)]
    monkeypatch.setattr(vitals,'now',lambda:current[0])
    return current


def test_only_five_stats_and_remaining_rerolls(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c,factory=client
    auth(c)
    draft=c.post('/characters/draft',json={}).json()
    assert set(draft['stats'])=={'strength','stamina','intelligence','agility','luck'}
    with factory() as db:
        assert db.get(Character,draft['id']).rerolls==10
    rolled=c.post('/characters/reroll',json={}).json()
    assert rolled['rerolls_remaining']==9 and rolled['rerolls_used']==1
    with factory() as db:
        assert db.get(Character,draft['id']).rerolls==9


def test_search_cost_and_rest_percent_bounds(world,clock,monkeypatch):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c,factory,character=world
    with factory() as db:
        stored=db.get(Character,character['id'])
        stored.hp_current=1;stored.mp_current=0;stored.stamina_current=3;stored.stamina_updated_at=clock[0]
        db.commit()
    state=start(c);force_draw(monkeypatch,0)
    searched=act(c,state,'search').json()
    assert searched['vitals']['stamina_current']==2
    rested=act(c,searched,'rest').json()
    assert rested['vitals']['hp_current']==3 and rested['vitals']['mp_current']==2  # 5% of 40
    assert rested['vitals']['stamina_current']==1
    force_draw(monkeypatch,25)
    rested2=act(c,rested,'rest').json()
    assert rested2['vitals']['hp_current']==15 and rested2['vitals']['mp_current']==14  # +30%
    assert rested2['vitals']['stamina_current']==0
    for _ in range(4):
        clock[0]+=timedelta(minutes=5)
        rested2=act(c,rested2,'rest').json()
    assert rested2['vitals']['hp_current']==40 and rested2['vitals']['hp_percent']==100
    assert rested2['vitals']['mp_current']==40 and rested2['vitals']['mp_percent']==100
    assert rested2['vitals']['stamina_current']==0


def test_zero_stamina_rejects_search_without_advancing(world,clock,monkeypatch):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c,factory,character=world
    with factory() as db:
        stored=db.get(Character,character['id']);stored.stamina_current=0;stored.stamina_updated_at=clock[0];db.commit()
    state=start(c);force_draw(monkeypatch,0)
    response=act(c,state,'search')
    assert response.status_code==409
    assert core_state(c.get('/exploration/state').json())==core_state(state)
    rested=act(c,state,'rest')
    assert rested.status_code==409
    assert core_state(c.get('/exploration/state').json())==core_state(state)


def test_offline_stamina_ticks_countdowns_and_no_banked_recovery(world,clock,monkeypatch):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c,factory,character=world
    origin=clock[0]
    with factory() as db:
        stored=db.get(Character,character['id']);stored.stamina_current=0;stored.stamina_updated_at=origin;db.commit()
    clock[0]=origin+timedelta(seconds=299)
    data=c.get('/characters/vitals').json()
    assert data['stamina_current']==0 and data['next_stamina_seconds']==1 and data['full_stamina_seconds']==901
    clock[0]=origin+timedelta(seconds=300)
    data=c.get('/characters/vitals').json()
    assert data['stamina_current']==1 and data['next_stamina_seconds']==300 and data['full_stamina_seconds']==900
    clock[0]=origin+timedelta(seconds=600)
    assert c.get('/characters/vitals').json()['stamina_current']==2
    clock[0]=origin+timedelta(seconds=5000)
    data=c.get('/characters/vitals').json()
    assert data['stamina_current']==4 and data['next_stamina_seconds']==0
    state=start(c);force_draw(monkeypatch,0)
    state=act(c,state,'search').json()
    assert state['vitals']['stamina_current']==3
    clock[0]=origin+timedelta(seconds=5299)
    data=c.get('/me').json()['character']['vitals']
    assert data['stamina_current']==3 and data['next_stamina_seconds']==1
    clock[0]=origin+timedelta(seconds=5300)
    assert c.get('/characters/vitals').json()['stamina_current']==4


def test_event_and_item_helpers_clamp_resources(world):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    _,factory,character=world
    with factory() as db:
        stored=db.get(Character,character['id'])
        vitals.apply_damage(stored,10000,10000)
        assert vitals.data(stored)['hp_percent']==0 and vitals.data(stored)['mp_percent']==0
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            vitals.restore_points(stored,10000,10000)
        stored.hp_current = 1
        vitals.restore_points(stored,10000,10000)
        assert vitals.data(stored)['hp_percent']==100 and vitals.data(stored)['mp_percent']==100
        assert stored.stamina_current==4


def test_encyclopedia_reveals_on_find_not_pickup_and_is_personal(world,monkeypatch):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c,factory,character=world
    maps=c.get('/maps').json()
    assert all(item['name']=='???' and item['weight_grams'] is None and not item['discovered'] for row in maps for item in row['items'])
    state=start(c);force_draw(monkeypatch,70)
    found=act(c,state,'search').json()
    catalog=c.get('/encyclopedia').json()
    known=next(item for row in catalog for item in row['items'] if item['item_id']==1)
    assert known['name']=='정체를 알 수 없는 버섯' and known['discovered']
    assert c.get('/inventory').json()['used_slots']==0
    given=act(c,found,'give_up').json()
    assert c.get('/encyclopedia').json()==catalog
    found=act(c,given,'search').json()
    with factory() as db:
        assert db.scalar(sa.select(sa.func.count()).select_from(Encyclopedia))==1
    c.post('/auth/logout',json={})
    other={'username':'other_user','password':CREDS['password']}
    c.post('/auth/signup',json=other);c.post('/auth/login',json=other);make_ready(c,'다른캐릭터')
    assert all(item['name']=='???' for row in c.get('/encyclopedia').json() for item in row['items'])


def test_v5_converts_once_and_backfills_existing_discoveries(tmp_path):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'v5.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0003_names_archive')
    insert_data(engine,3)
    with engine.connect() as db:
        command.upgrade(config_for(db),'0004_exploration_inventory')
    with engine.begin() as db:
        db.execute(sa.text('ALTER TABLE character ADD COLUMN hp_current INTEGER NULL'))  # Simulated partial DDL
        db.execute(sa.text('INSERT INTO inventory_entry (inventory_id,item_id,quantity) SELECT id,1,2 FROM inventory'))
        exploration=sa.Table('exploration',sa.MetaData(),autoload_with=engine)
        db.execute(exploration.insert().values(character_id=77,map_id=3,status='active',turn=2,version=3,pending_item_id=2,pending_quantity=1,
            history=[{'kind':'found','turn':1,'message':"'붉은 잎 약초'을 발견했다."}]))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0006_character_appearance')
    with engine.begin() as db:
        table=sa.Table('character',sa.MetaData(),autoload_with=engine)
        row=db.execute(sa.select(table)).mappings().one()
        assert row['rerolls']==7 and 'appearance' not in row['stats'] and 'height_cm' not in row['stats']
        assert row['hp_current']==40 and row['mp_current']==40 and row['stamina_current']==4
        assert {row[0] for row in db.execute(sa.text('SELECT item_id FROM encyclopedia'))}=={1,2,3}
        assert set(db.execute(sa.text('SELECT rerolls FROM deleted_character')).scalars())=={9}
        db.execute(sa.text('UPDATE character SET hp_current=0'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0006_character_appearance')
        assert db.execute(sa.text('SELECT rerolls FROM character')).scalar_one()==7
        assert db.execute(sa.text('SELECT hp_current FROM character')).scalar_one()==0
    assert head(engine)=='0006_character_appearance'
    engine.dispose()
