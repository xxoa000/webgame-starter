"""초기 키워드·대사 시드와 마이그레이션 재실행 보존을 검증한다."""
import importlib.util
from pathlib import Path
import sqlalchemy as sa
from alembic import command
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from test_alembic import config_for


def test_seed_counts_and_replay_preserves_edits(tmp_path):
    """기존 캐릭터를 강제 배정하지 않고 사용자 편집 원문을 보존한다."""
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'personality.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0010_posts')
    with engine.begin() as db:
        db.execute(sa.text("INSERT INTO users (id,username,password_hash) VALUES (1,'legacy','hash')"))
        db.execute(sa.text("INSERT INTO character (id,user_id,name,gender,age,bio,stats,rerolls,status) VALUES (1,1,'기존','female',17,'소개',:stats,5,'ready')"),{'stats':'{"strength":4,"stamina":4,"intelligence":4,"agility":4,"luck":4}'})
    with engine.connect() as db:
        command.upgrade(config_for(db),'head')
    with engine.begin() as db:
        assert db.execute(sa.text('SELECT COUNT(*) FROM personality_keyword')).scalar_one()==11
        assert db.execute(sa.text('SELECT COUNT(*) FROM game_script')).scalar_one()==178
        assert db.execute(sa.text('SELECT COUNT(*) FROM character_personality')).scalar_one()==0
        assert db.execute(sa.text('SELECT age,name_changes,age_changes FROM character')).one()==(17,0,0)
        assert db.execute(sa.text('SELECT COUNT(*) FROM users')).scalar_one()==1
        db.execute(sa.text("UPDATE game_script SET content='내가 수정한 원문' WHERE code='empty_COMMON_SPEECH'"))
        spec=importlib.util.spec_from_file_location('personality_revision',Path(__file__).resolve().parents[1]/'alembic/versions/0011_personality_scripts.py')
        revision=importlib.util.module_from_spec(spec);spec.loader.exec_module(revision)
        with Operations.context(MigrationContext.configure(db)):
            revision.upgrade()
        assert db.execute(sa.text('SELECT COUNT(*) FROM game_script')).scalar_one()==178
        assert db.execute(sa.text("SELECT content FROM game_script WHERE code='empty_COMMON_SPEECH'")).scalar_one()=='내가 수정한 원문'
        assert db.execute(sa.text('PRAGMA foreign_key_check')).all()==[]
    engine.dispose()
