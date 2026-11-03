"""조건·우선순위·가중 추첨·사용권·공개 범위와 출력 보존을 검증한다."""
from types import SimpleNamespace
from sqlalchemy import select
from test_flow import client
from test_exploration import world, start, act
from app.modules.characters.models import Character
from app.modules.users.models import User
from app.modules.scripts.models import ScriptPack, ScriptPackVersion, GameScript, UserScriptPack, CharacterScriptPack
from app.modules.scripts.service import select_output, matches, render, public_output

CONTEXT = {'character_name':'루아','map_name':'지역','item_name':'물자','monster_name':'괴물'}


def test_three_keyword_candidates_random_and_fallback(world, monkeypatch):
    """세 조건 일치 대사도 여러 후보 중 선택하며 미일치 시 단일 성격을 사용한다."""
    _,factory,character=world
    with factory() as db:
        c=db.get(Character,character['id'])
        monkeypatch.setattr('app.modules.scripts.service.secrets.randbelow',lambda size:0)
        first=select_output(db,c,'encounter',1,CONTEXT,[])
        speech=next(row for row in first if row['layer']=='SPEECH')
        monkeypatch.setattr('app.modules.scripts.service.secrets.randbelow',lambda size:size-1)
        second=select_output(db,c,'encounter',1,CONTEXT,[])
        other=next(row for row in second if row['layer']=='SPEECH')
        assert speech['script_id'] != other['script_id']
        assert db.get(GameScript,speech['script_id']).priority == 30
        assert db.get(GameScript,other['script_id']).priority == 30
        outer = next(link for link in c.personality if link.category == 'OUTER')
        outer.keyword_id = 2
        db.flush(); db.expire(c, ['personality'])
        single = next(row for row in select_output(db,c,'encounter',1,CONTEXT,[]) if row['layer']=='SPEECH')
        assert db.get(GameScript,single['script_id']).priority == 10
        for row in db.scalars(select(GameScript).where(GameScript.situation_code=='encounter', GameScript.layer=='SPEECH', GameScript.priority==10)):
            row.is_active = 0
        db.flush()
        common = next(row for row in select_output(db,c,'encounter',1,CONTEXT,[]) if row['layer']=='SPEECH')
        assert db.get(GameScript,common['script_id']).priority == 0
        assert len(public_output(first)) == 1
        assert public_output([{'layer':'THOUGHT','visibility':'PUBLIC','content':'비밀'}]) == []
        before=dict(c.stats)
        assert before == c.stats


def test_condition_groups_hp_and_safe_variables():
    """그룹의 AND·OR와 HP 범위, 안전한 치환 규칙을 검증한다."""
    def condition(group, key=None, map_id=None, low=None, high=None):
        """조건 판정에 필요한 최소 필드를 구성한다."""
        return SimpleNamespace(condition_group=group,keyword_id=key,map_id=map_id,hp_min_percent=low,hp_max_percent=high)
    rows=[condition(1,1),condition(1,11),condition(1,21,low=1,high=30),condition(2,4,map_id=3)]
    assert matches(rows,{1,11,21},1,30)
    assert not matches(rows,{1,11,21},1,31)
    assert not matches(rows,{1,11},1,20)
    assert matches(rows,{4},3,80)
    assert render('{character_name}: {item_name}',CONTEXT) == '루아: 물자'
    for text in ('{character_name.__class__}','{unknown}','{character_name!r}','{character_name:>1000000}'):
        assert render(text,CONTEXT) is None


def test_private_entitlements_and_revocation(world):
    """적용 행을 조작해도 타인의 원고는 사용권 없이는 선택되지 않는다."""
    _,factory,character=world
    with factory() as db:
        c=db.get(Character,character['id'])
        other=User(username='script_author',password_hash='hash');db.add(other);db.flush()
        pack=ScriptPack(code='PRIVATE_TEST',title='개인 대사',author_id=other.id,kind='PERSONAL');db.add(pack);db.flush()
        version=ScriptPackVersion(pack_id=pack.id,version=1,status='APPROVED');db.add(version);db.flush()
        script=GameScript(code='PRIVATE_LINE',version_id=version.id,situation_code='encounter',layer='SPEECH',visibility='PUBLIC',content='개인 전용 대사',priority=999,weight=100,is_active=1)
        db.add(script);db.add(CharacterScriptPack(character_id=c.id,version_id=version.id,mode='PREFER'));db.flush()
        outputs=select_output(db,c,'encounter',1,CONTEXT,[])
        assert all(row['script_id'] != script.id for row in outputs)
        db.add(UserScriptPack(user_id=c.user_id,version_id=version.id,source='GRANT'));db.flush()
        assert any(row['script_id']==script.id for row in select_output(db,c,'encounter',1,CONTEXT,[]))
        version.status='DISABLED';db.flush()
        assert all(row['script_id']!=script.id for row in select_output(db,c,'encounter',1,CONTEXT,[]))


def test_output_snapshot_survives_reload_and_original_edit(world, monkeypatch):
    """출력 시점 문장은 원본 수정이나 조회 요청으로 다시 추첨되지 않는다."""
    c,factory,_=world
    monkeypatch.setattr('app.modules.exploration.service.secrets.randbelow',lambda size:0)
    searched=act(c,start(c),'search').json()
    event=searched['history'][-1]
    assert event['scripts'] and event['event_key']
    before=event['scripts'][0]['content']
    with factory() as db:
        db.get(GameScript,event['scripts'][0]['script_id']).content='수정된 원본'
        db.commit()
    stored=c.get('/exploration/state').json()['history'][-1]
    assert stored['event_key']==event['event_key'] and stored['scripts'][0]['content']==before
