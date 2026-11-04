"""빈사·NPC 및 플레이어 구조·턴 규칙·버리기·무료 재화 거래를 검증한다."""
import pytest
from fastapi import HTTPException
from datetime import timedelta
from sqlalchemy import select,func
from test_flow import client
from test_exploration import world,start,act
from test_combat import battlefield
from app.database.base import utc_now
from app.modules.characters.models import Character,DeletedCharacter
from app.modules.users.models import User
from app.modules.items.models import Item
from app.modules.rescue.models import RescueRequest
from app.modules.exploration.models import Exploration


def down(battlefield):
    """남은 HP 1에서 치명상을 받도록 한다."""
    c,factory,character,state,item_id=battlefield
    with factory.begin() as db:
        db.get(Character,character['id']).hp_current=1
    response=act(c,state,'fight')
    assert response.status_code==200,response.text
    return c,factory,character,response.json(),item_id


def test_downed_and_abandon(battlefield):
    """치명상은 빈사이며 구조 포기 후에만 사망하고 한 번 보관된다."""
    c,factory,character,state,item_id=down(battlefield)
    assert state['downed'] and not state['dead'] and state['combat'] is None
    assert state['vitals']['hp_current']==1 and state['vitals']['condition']=='빈사'
    for action in ['search','rest','use_item','end']:
        assert act(c,state,action,item_id=item_id).status_code==409
    for path in ['/inventory/use','/inventory/discard']:
        assert c.post(path,json={'item_id':item_id}).status_code==409
    assert c.post('/shop/buy',json={'item_id':item_id,'quantity':1}).status_code==409
    assert c.post('/exploration/start',json={'map_id':2}).status_code==409
    assert c.post('/rescue/request',json={}).status_code==200
    result=c.post('/rescue/abandon',json={})
    assert result.status_code==200,result.text
    assert result.json()['dead'] and any(row['kind']=='abandon' for row in result.json()['history'])
    assert c.get('/exploration/state').json()['dead']
    assert c.post('/rescue/abandon',json={}).status_code==409
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(DeletedCharacter))==1
    assert c.post('/characters/draft',json={}).status_code==200


def test_npc_rescue(battlefield):
    """반복 요청은 기한을 늘리지 않고 NPC는 한 번만 구조한다."""
    c,factory,_,state,_=down(battlefield)
    first=c.post('/rescue/request',json={}).json()
    again=c.post('/rescue/request',json={}).json()
    assert first['rescue']['due_at']==again['rescue']['due_at']
    with factory.begin() as db:
        db.scalar(select(RescueRequest)).due_at=utc_now()-timedelta(seconds=1)
    rescued=c.get('/exploration/state').json()
    assert not rescued['downed'] and rescued['status']=='ended'
    assert rescued['vitals']['hp_current']==12 and rescued['rescue']['status']=='rescued'
    assert c.get('/exploration/state').json()['version']==rescued['version']


def test_items_free_and_discard(battlefield):
    """전투 회복은 반격·턴 소모가 없으며 보유량만 버릴 수 있다."""
    c,factory,character,state,item_id=battlefield
    with factory.begin() as db:
        db.get(Character,character['id']).hp_current=10
    healed=act(c,state,'use_item',item_id=item_id).json()
    assert healed['turn']==state['turn'] and healed['vitals']['hp_current']==20
    inventory=c.get('/inventory').json()
    assert inventory['items'][0]['hp_restore']==10 and inventory['money']==1000
    assert c.post('/inventory/discard',json={'item_id':item_id,'quantity':2}).status_code==409
    assert c.post('/inventory/discard',json={'item_id':item_id}).status_code==200
    assert c.get('/inventory').json()['used_slots']==0


def test_rest_cost(world):
    """휴식은 턴과 스태미나를 1씩 소모한다."""
    c,factory,character=world
    state=start(c)
    rested=act(c,state,'rest').json()
    assert rested['turn']==state['turn']+1 and rested['vitals']['stamina_current']==state['vitals']['stamina_current']-1
    with factory.begin() as db:
        stored=db.get(Character,character['id']);stored.stamina_current=0;stored.stamina_updated_at=utc_now()
    assert act(c,rested,'rest').status_code==409


def test_shop_atomic_trade(world):
    """거래는 서버 가격을 사용하며 수량·무게 오류 시 잔액은 보존된다."""
    c,factory,_=world
    with factory.begin() as db:
        item=Item(name='밀봉 생수',description='물',kind='farming',weight_grams=1000,buy_price=50,sell_price=15)
        db.add(item);db.flush();item_id=item.id
    bought=c.post('/shop/buy',json={'item_id':item_id,'quantity':2})
    assert bought.status_code==200,bought.text
    assert bought.json()['money']==900 and bought.json()['items'][0]['quantity']==2
    sold=c.post('/shop/sell',json={'item_id':item_id,'quantity':1}).json()
    assert sold['money']==915 and sold['items'][0]['quantity']==1
    assert c.post('/shop/sell',json={'item_id':item_id,'quantity':2}).status_code==409
    for qty in [0,True,-1,1.5]:
        assert c.post('/shop/buy',json={'item_id':item_id,'quantity':qty}).status_code==422
    assert c.post('/shop/buy',json={'item_id':item_id,'quantity':1,'price':0}).status_code==422
    with factory.begin() as db:
        db.scalar(select(User)).money=100000
    assert c.post('/shop/buy',json={'item_id':item_id,'quantity':40}).status_code==409
    assert c.get('/inventory').json()['money']==100000


def test_player_rescue(battlefield):
    """동일 맵의 플레이어 구조는 양쪽 상태와 비용을 반영한다."""
    from app.modules.rescue.service import help_player
    from app.modules.characters.vitals import initialize
    c,factory,_,_,_=down(battlefield)
    requested=c.post('/rescue/request',json={}).json()
    with factory.begin() as db:
        user=User(username='helper_01',password_hash='hash');db.add(user);db.flush()
        helper=Character(user_id=user.id,name='구조자',name_key='구조자',gender='male',age=20,bio='',status='ready',stats={key:4 for key in ('strength','stamina','intelligence','agility','luck')},rerolls=0)
        db.add(helper);db.flush();initialize(helper)
        db.add(Exploration(character_id=helper.id,map_id=1,status='active',turn=0,version=1,history=[],pending_quantity=0));helper_id=user.id
    with factory.begin() as db:
        session=db.scalar(select(Exploration).join(Character, Character.id==Exploration.character_id).where(Character.user_id==helper_id))
        session.map_id=3
    with pytest.raises(HTTPException) as error:
        with factory() as db:
            help_player(db,helper_id,requested['rescue']['id'])
    assert error.value.status_code==409
    with factory.begin() as db:
        session=db.scalar(select(Exploration).join(Character, Character.id==Exploration.character_id).where(Character.user_id==helper_id))
        session.map_id=1
    with factory() as db:
        assert help_player(db,helper_id,requested['rescue']['id'])['rescued']
    rescued=c.get('/exploration/state').json()
    assert not rescued['downed'] and rescued['rescue']['helper']=='플레이어'
    with factory() as db:
        assert db.scalar(select(Character).where(Character.user_id==helper_id)).stamina_current==3


def test_migration_preserves_data(tmp_path):
    """기존 사용자·캐릭터·물품을 보존하며 잔액과 구조 구조를 추가한다."""
    import importlib.util
    from pathlib import Path
    import sqlalchemy as sa
    from alembic.operations import Operations
    from alembic.runtime.migration import MigrationContext
    spec=importlib.util.spec_from_file_location('rescue_shop_revision',Path(__file__).resolve().parents[1]/'alembic/versions/0015_rescue_shop.py')
    revision=importlib.util.module_from_spec(spec);spec.loader.exec_module(revision)
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'rescue_shop.db'))
    with engine.begin() as db:
        db.exec_driver_sql('CREATE TABLE users(id INTEGER PRIMARY KEY, username VARCHAR(24))')
        db.exec_driver_sql('CREATE TABLE character(id INTEGER PRIMARY KEY, name VARCHAR(24))')
        db.exec_driver_sql('CREATE TABLE map(id INTEGER PRIMARY KEY)')
        db.exec_driver_sql('CREATE TABLE item(id INTEGER PRIMARY KEY, name VARCHAR(100))')
        db.exec_driver_sql("INSERT INTO users VALUES(1,'existing')")
        db.exec_driver_sql("INSERT INTO character VALUES(1,'기존 캐릭터')")
        db.exec_driver_sql("INSERT INTO item VALUES(1,'멸균 붕대')")
        with Operations.context(MigrationContext.configure(db)):
            revision.upgrade()
        assert db.exec_driver_sql('SELECT username,money FROM users').one()==('existing',1000)
        assert db.exec_driver_sql('SELECT name,downed FROM character').one()==('기존 캐릭터',0)
        assert db.exec_driver_sql('SELECT buy_price,sell_price FROM item').one()==(80,25)
        assert 'rescue_request' in sa.inspect(db).get_table_names()
        with Operations.context(MigrationContext.configure(db)):
            revision.downgrade()
        assert db.exec_driver_sql('SELECT username FROM users').scalar_one()=='existing'
    engine.dispose()
