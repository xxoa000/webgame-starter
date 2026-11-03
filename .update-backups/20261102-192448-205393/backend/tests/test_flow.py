import os
os.environ['DATABASE_URL'] = 'sqlite://'
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app, get_db, hasher
from app.db import Base
from app.models import User
from app.config import STAT_RANGES
import pytest

@pytest.fixture
def client():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    def override():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app, headers={'Origin':'http://localhost:5174'}) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()

CREDS={'username':'tester_01','password':'test-password-123'}
def auth(client):
    assert client.post('/auth/signup',json=CREDS).status_code == 201
    assert client.post('/auth/login',json=CREDS).status_code == 200

def test_signup_password_and_session(client):
    c, factory = client
    assert c.get('/auth/check-username',params={'username':'tester_01'}).json()['available']
    auth(c)
    assert not c.get('/auth/check-username',params={'username':'TESTER_01'}).json()['available']
    assert c.post('/auth/signup',json=CREDS).status_code == 409
    with factory() as db:
        user=db.scalar(select(User))
        assert user.password_hash != CREDS['password']
        assert user.password_hash.startswith('$argon2')
        assert hasher.verify(CREDS['password'],user.password_hash)
    assert c.get('/me').json()['username']=='tester_01'
    assert c.post('/auth/logout',json={}).status_code==200
    assert c.get('/me').status_code==401
    assert c.post('/auth/login',json={**CREDS,'password':'wrong-password'}).status_code==401

def test_character_lifecycle(client):
    c,_=client
    auth(c)
    first=c.post('/characters/draft',json={}).json()
    assert first['rerolls_remaining']==10
    assert c.post('/characters/draft',json={}).json()==first
    for i in range(10):
        response=c.post('/characters/reroll',json={})
        assert response.status_code==200
        data=response.json()
        assert data['rerolls_remaining']==9-i
        assert sum(data['stats'][key] for key in ('strength','stamina','intelligence','agility','luck'))==20
        assert all(lo<=data['stats'][key]<=hi for key,(lo,hi) in STAT_RANGES.items())
    assert c.post('/characters/reroll',json={}).status_code==409
    # Client-supplied stat edits are ignored; finalization accepts profile only.
    stats=data['stats']
    response=c.post('/characters/finalize',json={'name':'루아','gender':'female','age':12,'bio':'첫 번째 캐릭터','stats':{'strength':999}})
    assert response.status_code==200
    assert response.json()['stats']==stats
    assert response.json()['status']=='ready'
    assert c.post('/characters/reroll',json={}).status_code==409
    assert c.post('/characters/finalize',json={'name':'다른 이름','gender':'male','age':12}).status_code==409
    assert c.get('/me').json()['character']['name']=='루아'

def test_isolation_and_validation(client):
    c,_=client
    assert c.post('/characters/draft',json={}).status_code==401
    assert c.post('/auth/signup',json={**CREDS,'password':'short'}).status_code==422
    auth(c)
    c.post('/characters/draft',json={})
    assert c.post('/characters/finalize',json={'name':' ','gender':'female','age':12}).status_code==422
    assert c.post('/characters/finalize',json={'name':'루아','gender':'invalid','age':12}).status_code==422
    c.post('/auth/logout',json={})
    other={'username':'tester_02','password':CREDS['password']}
    c.post('/auth/signup',json=other)
    c.post('/auth/login',json=other)
    assert c.get('/me').json()['character'] is None
    assert c.post('/characters/reroll',json={}).status_code==409
    assert c.post('/characters/draft',json={},headers={'Origin':'https://attacker.example'}).status_code==403


def test_stat_budget_and_age(client):
    from app.main import roll
    from app.config import CORE_STATS
    for _ in range(1000):
        stats = roll()
        assert sum(stats[key] for key in CORE_STATS) == 20
        assert all(1 <= stats[key] <= 16 for key in CORE_STATS)
    c, _ = client
    auth(c)
    c.post('/characters/draft', json={})
    for age in (9, 18, 10.5, "12", True, None):
        assert c.post('/characters/finalize', json={'name':'테스트','gender':'female','age':age}).status_code == 422
    assert c.post('/characters/finalize', json={'name':'테스트','gender':'female','age':17}).status_code == 200
    assert c.get('/me').json()['character']['age'] == 17


def make_ready(c, name='루아'):
    c.post('/characters/draft', json={})
    response = c.post('/characters/finalize', json={'name':name,'gender':'female','age':12,'bio':'보존할 소개'})
    assert response.status_code == 200
    return response.json()


def test_delete_confirmation_archive_and_reuse(client):
    from app.models import Character, DeletedCharacter
    c, factory = client
    auth(c)
    for _ in range(2):
        data = make_ready(c)
        assert not c.get('/characters/check-name', params={'name':'루아'}).json()['available']
        assert c.post('/characters/delete', json={'character_id':data['id'],'name':'다른 이름'}).status_code == 422
        assert c.get('/me').json()['character']['name'] == '루아'
        assert c.post('/characters/delete', json={'character_id':data['id']+1,'name':'루아'}).status_code == 404
        assert c.post('/characters/delete', json={'character_id':data['id'],'name':'루아'}).status_code == 200
        assert c.get('/me').json()['character'] is None
        assert c.get('/characters/check-name', params={'name':'루아'}).json()['available']
        assert c.post('/characters/delete', json={'character_id':data['id'],'name':'루아'}).status_code == 404
    with factory() as db:
        assert db.scalar(select(Character)) is None
        history = db.scalars(select(DeletedCharacter)).all()
        assert len(history) == 2
        assert history[0].user_id == history[1].user_id
        for entry in history:
            assert entry.name == '루아'
            assert entry.age == 12 and entry.gender == 'female'
            assert entry.bio == '보존할 소개'
            assert entry.deleted_at is not None and entry.status == 'ready'
        assert history[-1].stats == data['stats']


def test_duplicate_name_and_ownership(client):
    from app.models import Character
    from app.names import name_key
    from sqlalchemy.exc import IntegrityError
    c, factory = client
    auth(c)
    data = make_ready(c, 'Alice')
    c.post('/auth/logout', json={})
    other = {'username':'tester_02','password':CREDS['password']}
    c.post('/auth/signup', json=other)
    c.post('/auth/login', json=other)
    assert c.post('/characters/delete', json={'character_id':data['id'],'name':'Alice'}).status_code == 404
    assert not c.get('/characters/check-name', params={'name':' ALICE '}).json()['available']
    c.post('/characters/draft', json={})
    assert c.post('/characters/finalize', json={'name':'alice','gender':'male','age':10}).status_code == 409
    # DB UNIQUE is a second line of defense independent of endpoint prechecks.
    with factory() as db:
        draft = db.scalar(select(Character).where(Character.status == 'draft'))
        draft.name_key = name_key('alice')
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    assert c.post('/characters/finalize', json={'name':'다른이름','gender':'male','age':10}).status_code == 200
    c.post('/auth/logout', json={})
    assert c.get('/characters/check-name', params={'name':'name'}).status_code == 401
    assert c.post('/characters/delete', json={'character_id':data['id'],'name':'Alice'}).status_code == 401


def test_archive_failure_preserves_character(client):
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError
    from app.models import DeletedCharacter
    c, factory = client
    auth(c)
    data = make_ready(c)
    def fail(*args):
        raise IntegrityError('insert archive', {}, Exception('simulated storage failure'))
    event.listen(DeletedCharacter, 'before_insert', fail)
    try:
        with pytest.raises(IntegrityError):
            c.post('/characters/delete', json={'character_id':data['id'],'name':'루아'})
    finally:
        event.remove(DeletedCharacter, 'before_insert', fail)
    assert c.get('/me').json()['character']['name'] == '루아'
    with factory() as db:
        assert db.scalar(select(DeletedCharacter)) is None
