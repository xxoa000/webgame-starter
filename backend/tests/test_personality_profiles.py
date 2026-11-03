"""성격 분류 선택·관리자 삭제·인적사항 수정 한도와 보관을 검증한다."""
import pytest
from sqlalchemy import select
from test_flow import client, auth, make_ready, make_admin, CREDS
from app.modules.characters.models import Character, DeletedCharacter
from app.modules.personality.models import CharacterPersonality
from app.modules.users.models import User


def test_keyword_catalog_and_selection_validation(client):
    """지정된 11개 키워드와 생성 시 분류별 하나 선택을 보장한다."""
    c, factory = client
    keywords = c.get('/personality/keywords').json()
    assert len(keywords) == 11
    assert {row['name'] for row in keywords} == {'소심함','쾌활함','냉소적','예민함','겁많음','다정함','용감함','이기적임','선','중립','악'}
    auth(c); c.post('/characters/draft',json={})
    body = {'name':'성격테스트','gender':'male','age':50}
    assert c.post('/characters/finalize',json=body).status_code == 422
    for ids in ([1,2,21],[1,1,21],[1,11,999],[1,11],[True,11,21]):
        assert c.post('/characters/finalize',json={**body,'personality_keyword_ids':ids}).status_code == 422
    made = c.post('/characters/finalize',json={**body,'personality_keyword_ids':[4,14,23]})
    assert made.status_code == 200 and made.json()['age'] == 50
    assert {row['category'] for row in made.json()['personality']} == {'OUTER','INNER','ALIGNMENT'}
    assert c.post('/characters/personality',json={'personality_keyword_ids':[1,11,21]}).status_code == 409


def test_profile_changes_independent_limits_and_rollback(client):
    """동일 값과 실패 요청은 차감하지 않고 이름·나이를 각각 한 번만 변경한다."""
    c, factory = client; auth(c); made = make_ready(c)
    same = c.patch('/characters/profile',json={'name':made['name'],'age':12}).json()
    assert same['name_changes_remaining'] == same['age_changes_remaining'] == 1
    renamed = c.patch('/characters/profile',json={'name':'새 이름'}).json()
    assert renamed['name_changes_remaining'] == 0 and renamed['age_changes_remaining'] == 1
    assert c.patch('/characters/profile',json={'name':'또 이름','age':40}).status_code == 409
    assert c.get('/me').json()['character']['age'] == 12
    aged = c.patch('/characters/profile',json={'age':50}).json()
    assert aged['age_changes_remaining'] == 0
    assert c.patch('/characters/profile',json={'age':49}).status_code == 409
    assert c.patch('/characters/profile',json={'name':'새 이름','age':50,'bio':'첫 소개'}).status_code == 200
    for text in ('둘째 소개','셋째 소개'):
        assert c.patch('/characters/profile',json={'gender':'male','bio':text}).json()['bio'] == text
    for age in (9,51,10.5,True,None):
        assert c.patch('/characters/profile',json={'age':age}).status_code == 422
    assert c.patch('/characters/profile',json={'name_changes':0}).status_code == 422
    assert c.patch('/characters/profile',json={'stats':{'strength':999}}).status_code == 422


def test_duplicate_name_failure_keeps_chance(client):
    """다른 활성 이름과의 충돌은 변경 기회를 소비하지 않는다."""
    c, factory = client; auth(c); make_ready(c, '원래이름')
    c.post('/auth/logout',json={})
    creds={'username':'second_owner','password':CREDS['password']}
    c.post('/auth/signup',json=creds);c.post('/auth/login',json=creds);make_ready(c,'사용중이름')
    c.post('/auth/logout',json={});c.post('/auth/login',json=CREDS)
    assert c.patch('/characters/profile',json={'name':'사용중이름'}).status_code == 409
    assert c.get('/me').json()['character']['name_changes_remaining'] == 1


@pytest.mark.parametrize('role',[0,1])
def test_only_admin_can_delete(client, role):
    """일반 사용자와 스탭의 직접 삭제 API 호출을 차단한다."""
    c, factory = client;auth(c);made=make_ready(c)
    with factory() as db:
        db.scalar(select(User)).auth=role;db.commit()
    assert c.post('/characters/delete',json={'character_id':made['id'],'name':made['name']}).status_code == 403
    make_admin(factory)
    assert c.post('/characters/delete',json={'character_id':made['id'],'name':'틀린 이름'}).status_code == 422
    assert c.post('/characters/delete',json={'character_id':made['id'],'name':made['name']}).status_code == 200
    with factory() as db:
        archived=db.scalar(select(DeletedCharacter))
        assert len(archived.personality_snapshot) == 3
        assert db.scalar(select(CharacterPersonality)) is None


def test_legacy_character_selects_once(client):
    """이전 캐릭터는 강제 배정 없이 최초 성격 선택을 완료할 수 있다."""
    c,factory=client;auth(c);made=make_ready(c)
    with factory() as db:
        db.query(CharacterPersonality).filter_by(character_id=made['id']).delete();db.commit()
    assert c.get('/me').json()['character']['personality'] == []
    assert c.post('/exploration/start',json={'map_id':999}).status_code == 409
    chosen=c.post('/characters/personality',json={'personality_keyword_ids':[2,12,22]})
    assert chosen.status_code == 200 and len(chosen.json()['personality']) == 3
    assert c.post('/characters/personality',json={'personality_keyword_ids':[1,11,21]}).status_code == 409


def test_admin_deletes_other_owner_and_preserves_owner_link(client):
    """관리자 삭제 이력은 실행자가 아니라 원래 소유자에게 연결한다."""
    c,factory=client;auth(c);make_admin(factory)
    c.post('/auth/logout',json={})
    other={'username':'delete_target','password':CREDS['password']}
    c.post('/auth/signup',json=other);c.post('/auth/login',json=other);target=make_ready(c,'다른피계약자')
    with factory() as db:
        owner_id=db.scalar(select(User.id).where(User.username=='delete_target'))
    c.post('/auth/logout',json={});c.post('/auth/login',json=CREDS)
    assert c.post('/characters/delete',json={'character_id':target['id'],'name':target['name']}).status_code==200
    with factory() as db:
        archived=db.scalar(select(DeletedCharacter))
        assert archived.user_id==owner_id and len(archived.personality_snapshot)==3


def test_same_normalized_name_can_be_edited_once(client):
    """본인 이름의 대소문자 변경은 다른 소유자의 이름 중복과 구분한다."""
    c,_=client;auth(c);make_ready(c,'Alice')
    assert not c.get('/characters/check-name',params={'name':'alice'}).json()['available']
    assert c.get('/characters/check-name',params={'name':'alice','for_profile':True}).json()['available']
    result=c.patch('/characters/profile',json={'name':'alice'})
    assert result.status_code==200 and result.json()['name_changes_remaining']==0
