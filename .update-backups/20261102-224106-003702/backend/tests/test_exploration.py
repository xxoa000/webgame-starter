import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import select, func, text
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from test_flow import client, auth, make_ready, CREDS
from app.modules.items.models import Item
from app.modules.inventory.models import Inventory, InventoryEntry
from app.modules.exploration.models import Exploration
from app.modules.characters.models import DeletedCharacter


@pytest.fixture
def world(client):
    c, factory = client
    with factory() as db:
        db.execute(text('PRAGMA foreign_keys=ON'))
        assert db.execute(text('PRAGMA foreign_keys')).scalar_one() == 1
        spec = importlib.util.spec_from_file_location('world_seed',Path(__file__).resolve().parents[1]/'alembic/versions/0004_exploration_inventory.py')
        revision=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(revision)
        with Operations.context(MigrationContext.configure(db.connection())):
            revision.seed_world()
        db.commit()
    auth(c)
    character = make_ready(c)
    return c, factory, character


def start(c, map_id=1):
    response=c.post('/exploration/start',json={'map_id':map_id})
    assert response.status_code==200, response.text
    return response.json()


def act(c,state,action,**extra):
    return c.post('/exploration/action',json={'action':action,'exploration_id':state['id'],'version':state['version'],**extra})


def force_draw(monkeypatch, value):
    monkeypatch.setattr('app.modules.exploration.service.secrets.randbelow', lambda total:value)


def test_initial_inventory_maps_and_probabilities(world):
    c, factory, character=world
    with factory() as db:
        assert db.scalar(select(Inventory).where(Inventory.character_id==character['id'])) is not None
    inventory=c.get('/inventory').json()
    assert inventory['used_slots']==0 and inventory['slot_capacity']==10
    assert inventory['max_weight_grams']==30000 and inventory['current_weight_grams']==0
    maps=c.get('/maps').json()
    forest=next(row for row in maps if row['id']==1)
    assert forest['empty_probability']==0.7
    assert [row['probability'] for row in forest['items']]==[0.25,0.05]
    assert {row['item_id'] for row in maps[0]['items']}.isdisjoint({row['item_id'] for row in maps[1]['items']})


def test_pending_state_pause_resume_and_stacking(world,monkeypatch):
    c, factory, character=world
    state=start(c)
    assert start(c)==state
    force_draw(monkeypatch,70)
    found=act(c,state,'search').json()
    assert found['pending_item']['item_id']==1 and found['turn']==1
    assert act(c,found,'search').status_code==409
    assert act(c,found,'rest').status_code==409
    # Profile / inventory subwindows perform reads only and preserve the full state.
    c.get('/me'); c.get('/inventory')
    assert c.get('/exploration/state').json()==found
    c.post('/auth/logout',json={})
    c.post('/auth/login',json=CREDS)
    assert c.get('/exploration/state').json()==found
    taken=act(c,found,'take').json()
    assert taken['pending_item'] is None and taken['turn']==1
    assert act(c,found,'take').status_code==409
    assert c.get('/inventory').json()['items'][0]['quantity']==1
    found2=act(c,taken,'search').json()
    taken2=act(c,found2,'take').json()
    inventory=c.get('/inventory').json()
    assert inventory['used_slots']==1 and inventory['items'][0]['quantity']==2
    assert inventory['current_weight_grams']==400
    assert act(c,taken2,'take').status_code==409


def test_empty_rare_rest_give_up_end_and_map_change(world,monkeypatch):
    c, _, _=world
    state=start(c)
    assert c.post('/exploration/start',json={'map_id':3}).status_code==409
    force_draw(monkeypatch,0)
    empty=act(c,state,'search').json()
    assert empty['pending_item'] is None and empty['history'][-1]['kind']=='empty'
    rested=act(c,empty,'rest').json()
    assert rested['turn']==2
    force_draw(monkeypatch,95)
    rare=act(c,rested,'search').json()
    assert rare['pending_item']['item_id']==2
    given=act(c,rare,'give_up').json()
    assert c.get('/inventory').json()['used_slots']==0
    ended=act(c,given,'end').json()
    assert ended['status']=='ended'
    assert act(c,ended,'search').status_code==409
    state3=start(c,3)
    assert state3['version']>ended['version'] and state3['turn']==0
    assert act(c,given,'search').status_code==409
    force_draw(monkeypatch,55)
    herbs=act(c,state3,'search').json()
    assert herbs['pending_item']['item_id']==3


def test_exact_weight_limit_and_failed_pickup_retains_pending(world,monkeypatch):
    c,factory,_=world
    with factory() as db:
        inv=db.scalar(select(Inventory))
        db.add(InventoryEntry(inventory_id=inv.id,item_id=1,quantity=149))
        db.commit()
    state=start(c); force_draw(monkeypatch,70)
    found=act(c,state,'search').json()
    taken=act(c,found,'take').json()
    assert c.get('/inventory').json()['current_weight_grams']==30000
    over=act(c,taken,'search').json()
    assert act(c,over,'take').status_code==409
    assert c.get('/exploration/state').json()==over
    assert c.get('/inventory').json()['items'][0]['quantity']==150
    assert act(c,over,'give_up').status_code==200


def test_ten_distinct_slots_allow_existing_stack_but_reject_new_kind(world,monkeypatch):
    c,factory,_=world
    with factory() as db:
        inv=db.scalar(select(Inventory))
        for index in range(10):
            item=Item(name=f'테스트{index}',description='',weight_grams=1,kind='crafted')
            db.add(item);db.flush()
            db.add(InventoryEntry(inventory_id=inv.id,item_id=item.id,quantity=1))
        db.commit()
    state=start(c); force_draw(monkeypatch,70)
    found=act(c,state,'search').json()
    assert act(c,found,'take').status_code==409
    assert c.get('/inventory').json()['used_slots']==10
    assert c.get('/exploration/state').json()['pending_item']['item_id']==1
    # Replace one test slot with the already-held mushroom: 10 slots still allow stacking.
    with factory() as db:
        entry=db.scalar(select(InventoryEntry).order_by(InventoryEntry.id))
        entry.item_id=1
        db.commit()
    assert act(c,found,'take').status_code==200
    inventory=c.get('/inventory').json()
    assert inventory['used_slots']==10
    assert next(row for row in inventory['items'] if row['item_id']==1)['quantity']==2


def test_account_isolation_and_payload_tampering(world,monkeypatch):
    c,_,_=world
    state=start(c); force_draw(monkeypatch,70)
    found=act(c,state,'search').json()
    assert act(c,found,'take',item_id=999,quantity=999).status_code==422
    assert c.get('/inventory').json()['used_slots']==0
    c.post('/auth/logout',json={})
    assert c.get('/inventory').status_code==401
    assert c.get('/maps').status_code==401
    other={'username':'other_user','password':CREDS['password']}
    c.post('/auth/signup',json=other);c.post('/auth/login',json=other)
    assert c.get('/inventory').status_code==409
    make_ready(c,'다른캐릭터')
    assert c.get('/inventory').json()['used_slots']==0
    assert c.get('/exploration/state').json() is None
    other_state=start(c)
    assert act(c,found,'take').status_code==409
    assert c.get('/exploration/state').json()==other_state


def test_character_delete_cascades_gameplay_only(world,monkeypatch):
    c,factory,character=world
    state=start(c);force_draw(monkeypatch,70)
    found=act(c,state,'search').json();act(c,found,'take')
    assert c.post('/characters/delete',json={'character_id':character['id'],'name':character['name']}).status_code==200
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Inventory))==0
        assert db.scalar(select(func.count()).select_from(InventoryEntry))==0
        assert db.scalar(select(func.count()).select_from(Exploration))==0
        assert db.scalar(select(func.count()).select_from(DeletedCharacter))==1
    make_ready(c,'새캐릭터')
    assert c.get('/inventory').json()['used_slots']==0
    newer=start(c)
    assert newer['id']!=state['id']
    assert act(c,state,'search').status_code==409


def test_future_world_tables_and_foreign_keys(world):
    from sqlalchemy import inspect
    _,factory,_=world
    with factory() as db:
        inspector=inspect(db.connection())
        assert {column['name'] for column in inspector.get_columns('grimoire')} == {'id','magic_name','description','power','mana_cost'}
        assert {'main_item_id','sub_item1_id','sub_item2_id','result_item_id'} <= {column['name'] for column in inspector.get_columns('recipe')}
        for table,targets in {'map_farming_item':{'map','farming_item'},'map_monster':{'map','monster'},'monster_drop_item':{'monster','drop_item'},'recipe':{'item'}}.items():
            assert targets=={constraint['referred_table'] for constraint in inspector.get_foreign_keys(table)}
