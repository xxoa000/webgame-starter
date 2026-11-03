"""기능별 동작과 데이터 보존 조건을 검증한다."""
import os
os.environ['DATABASE_URL'] = 'sqlite://'
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import get_db
from app.core.security import hasher
from app.database import Base
from app.modules.users.models import User
from app.modules.characters.rules import STAT_RANGES
import pytest

@pytest.fixture
def client(monkeypatch):
    """격리된 테스트 DB와 API 클라이언트를 제공한다."""
    monkeypatch.setattr("app.main.assert_schema_current", lambda: None)
    monkeypatch.setattr("app.modules.users.maintenance.run_daily", lambda: 0)
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    from app.modules.personality.seed import seed_initial
    with engine.begin() as connection:
        seed_initial(connection)
    def override():
        """테스트용 DB 세션을 요청에 주입한다."""
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override
    with TestClient(app, headers={'Origin':'http://localhost:5174'}) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()

CREDS={'username':'tester_01','password':'test-password-123'}
def auth(client):
    """테스트 계정을 생성하고 로그인한다."""
    assert client.post('/auth/signup',json=CREDS).status_code == 201
    assert client.post('/auth/login',json=CREDS).status_code == 200

def test_signup_password_and_session(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
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
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
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
    response=c.post('/characters/finalize',json={'personality_keyword_ids':[1,11,21],'name':'루아','gender':'female','age':12,'bio':'첫 번째 캐릭터','stats':{'strength':999}})
    assert response.status_code==200
    assert response.json()['stats']==stats
    assert response.json()['status']=='ready'
    assert c.post('/characters/reroll',json={}).status_code==409
    assert c.post('/characters/finalize',json={'personality_keyword_ids':[1,11,21],'name':'다른 이름','gender':'male','age':12}).status_code==409
    assert c.get('/me').json()['character']['name']=='루아'

def test_isolation_and_validation(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c,_=client
    assert c.post('/characters/draft',json={}).status_code==401
    assert c.post('/auth/signup',json={**CREDS,'password':'short'}).status_code==422
    auth(c)
    c.post('/characters/draft',json={})
    assert c.post('/characters/finalize',json={'personality_keyword_ids':[1,11,21],'name':' ','gender':'female','age':12}).status_code==422
    assert c.post('/characters/finalize',json={'personality_keyword_ids':[1,11,21],'name':'루아','gender':'invalid','age':12}).status_code==422
    c.post('/auth/logout',json={})
    other={'username':'tester_02','password':CREDS['password']}
    c.post('/auth/signup',json=other)
    c.post('/auth/login',json=other)
    assert c.get('/me').json()['character'] is None
    assert c.post('/characters/reroll',json={}).status_code==409
    assert c.post('/characters/draft',json={},headers={'Origin':'https://attacker.example'}).status_code==403


def test_stat_budget_and_age(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    from app.modules.characters.stats import roll
    from app.modules.characters.rules import CORE_STATS
    for _ in range(1000):
        stats = roll()
        assert sum(stats[key] for key in CORE_STATS) == 20
        assert all(1 <= stats[key] <= 16 for key in CORE_STATS)
    c, _ = client
    auth(c)
    c.post('/characters/draft', json={})
    for age in (9, 51, 10.5, "12", True, None):
        assert c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':'테스트','gender':'female','age':age}).status_code == 422
    assert c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':'테스트','gender':'female','age':17}).status_code == 200
    assert c.get('/me').json()['character']['age'] == 17


def make_ready(c, name='루아'):
    """테스트 캐릭터 생성을 완료한다."""
    c.post('/characters/draft', json={})
    response = c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':name,'gender':'female','age':12,'bio':'보존할 소개'})
    assert response.status_code == 200
    return response.json()


def test_delete_confirmation_archive_and_reuse(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    from app.modules.characters.models import Character, DeletedCharacter
    c, factory = client
    auth(c)
    make_admin(factory)
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
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    from app.modules.characters.models import Character
    from app.modules.characters.names import name_key
    from sqlalchemy.exc import IntegrityError
    c, factory = client
    auth(c)
    data = make_ready(c, 'Alice')
    c.post('/auth/logout', json={})
    other = {'username':'tester_02','password':CREDS['password']}
    c.post('/auth/signup', json=other)
    c.post('/auth/login', json=other)
    assert c.post('/characters/delete', json={'character_id':data['id'],'name':'Alice'}).status_code == 403
    assert not c.get('/characters/check-name', params={'name':' ALICE '}).json()['available']
    c.post('/characters/draft', json={})
    assert c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':'alice','gender':'male','age':10}).status_code == 409
    # DB UNIQUE is a second line of defense independent of endpoint prechecks.
    with factory() as db:
        draft = db.scalar(select(Character).where(Character.status == 'draft'))
        draft.name_key = name_key('alice')
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
    assert c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':'다른이름','gender':'male','age':10}).status_code == 200
    c.post('/auth/logout', json={})
    assert c.get('/characters/check-name', params={'name':'name'}).status_code == 401
    assert c.post('/characters/delete', json={'character_id':data['id'],'name':'Alice'}).status_code == 401


def test_archive_failure_preserves_character(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    from sqlalchemy import event
    from sqlalchemy.exc import IntegrityError
    from app.modules.characters.models import DeletedCharacter
    c, factory = client
    auth(c)
    make_admin(factory)
    data = make_ready(c)
    def fail(*args):
        """테스트에 필요한 데이터와 검증 조건을 준비한다."""
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


def make_admin(factory):
    """삭제 검증에 사용하는 기존 테스트 계정에 관리자 권한을 부여한다."""
    with factory() as db:
        db.scalar(select(User).where(User.username == CREDS['username'])).auth = 9
        db.commit()
