from datetime import datetime
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.autogenerate import compare_metadata
from app.database.metadata import target_metadata
from app.database import checks

ROOT = Path(__file__).resolve().parents[1]


def config_for(connection):
    config = Config(str(ROOT/'alembic.ini'))
    config.attributes['connection'] = connection
    return config


def head(engine):
    with engine.connect() as db:
        return MigrationContext.configure(db).get_current_revision()


def initial(engine):
    with engine.connect() as db:
        command.upgrade(config_for(db), '0001_initial')
    with engine.begin() as db:
        db.execute(sa.text('DROP TABLE alembic_version'))


def insert_data(engine, stage):
    meta = sa.MetaData()
    client = sa.Table('client', meta, autoload_with=engine)
    character = sa.Table('character', meta, autoload_with=engine)
    session = sa.Table('login_session', meta, autoload_with=engine)
    stats = {'strength':4,'stamina':4,'intelligence':4,'agility':4,'luck':4,'appearance':80,'height_cm':170}
    if stage == 0:
        stats['strength'] = 50
    values = dict(id=77,user_id=5,name='루아',gender='female',bio='기존 소개',stats=stats,rerolls=3,status='ready')
    if stage >= 2:
        values['age'] = 13
    if stage == 3:
        from app.modules.characters.names import name_key
        values['name_key'] = name_key('루아')
    with engine.begin() as db:
        db.execute(client.insert().values(id=5,username='original',password_hash='preserve_hash'))
        db.execute(session.insert().values(token_hash='a'*64,user_id=5,expires_at=datetime(2030,1,1)))
        db.execute(character.insert().values(**values))
        if stage == 3:
            archive = sa.Table('deleted_character',meta,autoload_with=engine)
            for index in range(2):
                db.execute(archive.insert().values(id=index+1,original_character_id=60+index,user_id=5,
                    name='이전이름',gender='female',age=12,bio='삭제 이력',stats=stats,rerolls=1,status='ready',deleted_at=datetime(2026,1,1)))
    return stats


def test_fresh_database_and_startup_check(tmp_path, monkeypatch):
    engine = sa.create_engine('sqlite:///'+str(tmp_path/'fresh.db'))
    monkeypatch.setattr(checks,'engine',engine)
    with pytest.raises(RuntimeError,match='alembic upgrade head'):
        checks.assert_schema_current()
    with engine.connect() as db:
        command.upgrade(config_for(db),'head')
        assert compare_metadata(MigrationContext.configure(db),target_metadata) == []
    checks.assert_schema_current()
    assert head(engine) == '0003_names_archive'
    assert 'posts' not in sa.inspect(engine).get_table_names()
    engine.dispose()


@pytest.mark.parametrize('stage',[0,2,3])
def test_adopt_existing_database_preserves_data(tmp_path,stage):
    engine = sa.create_engine('sqlite:///'+str(tmp_path/f'old{stage}.db'))
    if stage == 3:
        target_metadata.create_all(engine)
    else:
        initial(engine)
        if stage == 2:
            with engine.begin() as db:
                db.execute(sa.text('ALTER TABLE character ADD COLUMN age INTEGER NULL'))
    original = insert_data(engine,stage)
    with engine.connect() as db:
        command.upgrade(config_for(db),'head')
    with engine.connect() as db:
        character = sa.Table('character',sa.MetaData(),autoload_with=engine)
        row = db.execute(sa.select(character)).mappings().one()
        assert row['id']==77 and row['user_id']==5 and row['rerolls']==3
        assert row['name']=='루아' and row['bio']=='기존 소개'
        assert row['stats']['appearance']==80 and row['stats']['height_cm']==170
        assert sum(row['stats'][key] for key in ('strength','stamina','intelligence','agility','luck'))==20
        if stage>=2:
            assert row['stats']==original and row['age']==13
        else:
            assert row['age'] is None
        assert db.execute(sa.text('SELECT password_hash FROM client')).scalar_one()=='preserve_hash'
        assert db.execute(sa.text('SELECT COUNT(*) FROM login_session')).scalar_one()==1
        count=db.execute(sa.text('SELECT COUNT(*) FROM deleted_character')).scalar_one()
        assert count==(2 if stage==3 else 0)
        before=row['stats']
    with engine.connect() as db:
        command.upgrade(config_for(db),'head')
    with engine.connect() as db:
        assert db.execute(sa.select(character.c.stats)).scalar_one()==before
    assert head(engine)=='0003_names_archive'
    engine.dispose()


def test_duplicate_names_stop_and_resume(tmp_path):
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'duplicate.db'))
    initial(engine)
    insert_data(engine,0)
    table=sa.Table('character',sa.MetaData(),autoload_with=engine)
    with engine.begin() as db:
        db.execute(sa.text("INSERT INTO client VALUES (6,'other','hash')"))
        db.execute(table.insert().values(id=78,user_id=6,name='루아',gender='male',bio='',stats={'strength':4,'stamina':4,'intelligence':4,'agility':4,'luck':4},rerolls=0,status='ready'))
    with engine.connect() as db:
        with pytest.raises(RuntimeError,match='중복 캐릭터 ID'):
            command.upgrade(config_for(db),'head')
    with engine.begin() as db:
        db.execute(sa.text("UPDATE character SET name='다른이름' WHERE id=78"))
    with engine.connect() as db:
        command.upgrade(config_for(db),'head')
    assert head(engine)=='0003_names_archive'
    engine.dispose()


def test_revision_generation_template(tmp_path):
    import shutil
    root=tmp_path/'backend'
    shutil.copytree(ROOT/'alembic',root/'alembic')
    shutil.copyfile(ROOT/'alembic.ini',root/'alembic.ini')
    config=Config(str(root/'alembic.ini'))
    revision=command.revision(config,message='add post fields')
    assert Path(revision.path).is_file()
    compile(Path(revision.path).read_text(),revision.path,'exec')
    assert revision.down_revision=='0003_names_archive'
