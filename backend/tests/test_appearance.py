"""프로필 프리셋 저장·성별 보존·소유권·삭제 보관과 마이그레이션을 검증한다."""
import sqlalchemy as sa
from alembic import command
from test_flow import client, auth, make_ready, CREDS
from test_alembic import config_for
from app.modules.characters.models import DeletedCharacter
from app.modules.characters.appearance import Appearance


def test_appearance_save_validation_and_archive(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory = client
    auth(c)
    make_ready(c, '외형테스트')
    from test_flow import make_admin
    make_admin(factory)
    before = c.get('/me').json()['character']
    appearance = Appearance(preset='portrait_06').model_dump()
    body = {'appearance': appearance}
    saved = c.post('/characters/appearance', json=body)
    assert saved.status_code == 200
    assert saved.json()['appearance'] == appearance
    assert saved.json()['gender'] == before['gender']
    assert saved.json()['stats'] == before['stats']
    assert c.post('/characters/appearance', json={'appearance': {'preset': 'missing'}}).status_code == 422
    assert saved.json()['vitals']['hp_current'] == before['vitals']['hp_current']
    assert c.get('/me').json()['character']['appearance'] == appearance
    assert c.post('/characters/appearance', json={**body, 'gender': 'other'}).status_code == 422
    assert c.post('/characters/appearance', json={**body, 'appearance': {**appearance, 'hair': 'invalid'}}).status_code == 422
    assert c.post('/characters/appearance', json={**body, 'appearance': {**appearance, 'strength': 999}}).status_code == 422
    assert c.post('/characters/delete', json={'character_id': before['id'], 'name': before['name']}).status_code == 200
    with factory() as db:
        assert db.scalar(sa.select(DeletedCharacter)).appearance == appearance


def test_common_parts_for_both_genders_and_isolation(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, _ = client
    assert c.post('/characters/appearance', json={'appearance':{}}).status_code == 401
    auth(c)
    c.post('/characters/draft', json={})
    assert c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':'선택','gender':'other','age':12}).status_code == 422
    made = c.post('/characters/finalize', json={'personality_keyword_ids':[1,11,21],'name':'공용머리','gender':'female','age':12,'appearance':{'hair':'crop','face':'sharp'}})
    assert made.status_code == 200
    appearance = made.json()['appearance']
    for number in range(1, 7):
        result = c.post('/characters/appearance', json={'appearance': {'preset': f'portrait_0{number}'}})
        assert result.status_code == 200
        assert result.json()['appearance']['preset'] == f'portrait_0{number}'
        assert result.json()['gender'] == 'female'
    c.post('/auth/logout', json={})
    other={'username':'appearance_other','password':CREDS['password']}
    c.post('/auth/signup', json=other); c.post('/auth/login', json=other)
    assert c.post('/characters/appearance', json={'appearance':appearance}).status_code == 409


def test_appearance_migration_preserves_legacy_and_replays(tmp_path):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'appearance.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0005_vitals_encyclopedia')
    with engine.begin() as db:
        db.execute(sa.text("INSERT INTO client (id,username,password_hash) VALUES (1,'old','hash')"))
        db.execute(sa.text("INSERT INTO character (id,user_id,name,gender,bio,stats,rerolls,status,hp_current) VALUES (1,1,'old','other','preserve',:stats,6,'ready',23)"), {'stats':'{"strength":4,"stamina":4,"intelligence":4,"agility":4,"luck":4}'})
    with engine.connect() as db:
        command.upgrade(config_for(db),'head')
        command.upgrade(config_for(db),'head')
        row=db.execute(sa.text('SELECT gender,bio,rerolls,hp_current,appearance FROM character')).one()
        assert tuple(row)==('other','preserve',6,23,None)
    assert 'appearance' in {c['name'] for c in sa.inspect(engine).get_columns('deleted_character')}
    engine.dispose()
