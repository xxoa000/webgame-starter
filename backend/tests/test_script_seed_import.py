"""CSV 코드 정규화와 초기 공통 대사 교체·재실행·롤백을 검증한다."""
from pathlib import Path
import pytest
from sqlalchemy import select, func
from test_flow import client
from app.modules.scripts.import_seed import load_seed, sync_seed
from app.modules.scripts.models import GameScript, GameScriptCondition, ScriptPack, ScriptPackVersion
from app.modules.personality.models import PersonalityKeyword

ROOT=Path(__file__).resolve().parents[2]


def seed_files():
    """프로젝트 최상위의 실제 배포 CSV를 검증해 읽는다."""
    return load_seed(ROOT/'SCRIPTS-SEED.csv',ROOT/'SCRIPT-CONDITIONS-SEED.csv')


def test_replace_and_repeat_keep_ids_and_other_packs(client):
    """기존 ID와 다른 묶음을 보존하며 333개로 교체하고 반복 실행해도 중복하지 않는다."""
    _,factory=client
    scripts,conditions=seed_files()
    with factory() as db:
        first_id=db.scalar(select(GameScript.id).where(GameScript.code=='empty_K1_1'))
        keyword_ids={row.code.lower():row.id for row in db.scalars(select(PersonalityKeyword))}
        pack=ScriptPack(code='personal_test',title='개인 원고',kind='PERSONAL')
        db.add(pack);db.flush()
        version=ScriptPackVersion(pack_id=pack.id,version=1,status='APPROVED')
        db.add(version);db.flush()
        personal=GameScript(code='private_test',version_id=version.id,situation_code='empty',layer='SPEECH',content='개인 원문',priority=10,weight=100,is_active=1)
        db.add(personal);db.commit()
    with factory.begin() as db:
        result=sync_seed(db,scripts,conditions)
        assert result['updated']==178 and result['inserted']==155 and result['removed']==0
    with factory() as db:
        assert db.scalar(select(GameScript.id).where(GameScript.code=='outer_shy_001'))==first_id
        assert db.scalar(select(GameScript.content).where(GameScript.code=='private_test'))=='개인 원문'
        assert db.scalar(select(func.count()).select_from(GameScript))==334
        assert db.scalar(select(func.count()).select_from(GameScriptCondition))==273
        assert {row.code:row.id for row in db.scalars(select(PersonalityKeyword))}==keyword_ids
        ids={row.code:row.id for row in db.scalars(select(GameScript))}
    with factory.begin() as db:
        result=sync_seed(db,scripts,conditions)
        assert result['updated']==333 and result['inserted']==0 and result['removed']==0
    with factory() as db:
        assert {row.code:row.id for row in db.scalars(select(GameScript))}==ids
        assert not db.scalar(select(GameScript.id).where(GameScript.code.like('seed_tmp_%')))
    from app.modules.personality.seed import seed_initial
    with factory.begin() as db:
        seed_initial(db.connection())
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(GameScript))==334
        assert db.scalar(select(PersonalityKeyword.id).where(PersonalityKeyword.code=='OUTER_SHY')) is None


def test_import_rollback_keeps_original_data(client):
    """교체 도중 실패하면 본문·코드·조건을 모두 이전 상태로 되돌린다."""
    _,factory=client
    scripts,conditions=seed_files()
    with pytest.raises(RuntimeError):
        with factory.begin() as db:
            sync_seed(db,scripts,conditions)
            raise RuntimeError('트랜잭션 중단 테스트')
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(GameScript))==178
        assert db.scalar(select(func.count()).select_from(GameScriptCondition))==160
        assert db.scalar(select(GameScript.id).where(GameScript.code=='empty_K1_1')) is not None
        assert db.scalar(select(PersonalityKeyword.id).where(PersonalityKeyword.code=='OUTER_SHY')) is not None


def test_other_pack_collision_refused(client):
    """개인 묶음에서 이미 사용한 코드는 덮어쓰지 않고 오류로 중단한다."""
    _,factory=client
    scripts,conditions=seed_files()
    with factory.begin() as db:
        pack=ScriptPack(code='personal_collision',title='충돌',kind='PERSONAL')
        db.add(pack);db.flush()
        version=ScriptPackVersion(pack_id=pack.id,version=1,status='APPROVED')
        db.add(version);db.flush()
        db.add(GameScript(code='outer_shy_001',version_id=version.id,situation_code='empty',layer='SPEECH',content='보존할 원문',priority=10,weight=100,is_active=1))
    with pytest.raises(ValueError,match='다른 원고 묶음'):
        with factory.begin() as db:
            sync_seed(db,scripts,conditions)
    with factory() as db:
        assert db.scalar(select(GameScript.content).where(GameScript.code=='outer_shy_001'))=='보존할 원문'
        assert db.scalar(select(GameScript.id).where(GameScript.code=='empty_K1_1')) is not None
