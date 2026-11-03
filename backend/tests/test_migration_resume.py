"""기능별 동작과 데이터 보존 조건을 검증한다."""
from datetime import datetime
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.operations import Operations
from test_alembic import config_for, head, insert_data


@pytest.mark.parametrize('stop_at',['item','exploration','inventory_entry'])
def test_resume_after_ddl_failure(tmp_path, monkeypatch, stop_at):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'partial.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0003_names_archive')
    insert_data(engine,3)
    original=Operations.create_table
    def fail(self,table_name,*args,**kwargs):
        """테스트에 필요한 데이터와 검증 조건을 준비한다."""
        if table_name==stop_at:
            raise RuntimeError('simulated DDL failure')
        return original(self,table_name,*args,**kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(Operations,'create_table',fail)
        with engine.connect() as db:
            with pytest.raises(RuntimeError,match='simulated DDL failure'):
                command.upgrade(config_for(db),'0004_exploration_inventory')
    assert head(engine)=='0003_names_archive'
    assert 'grimoire' in sa.inspect(engine).get_table_names()
    with engine.connect() as db:
        command.upgrade(config_for(db),'0004_exploration_inventory')
        assert db.execute(sa.text('SELECT COUNT(*) FROM item')).scalar_one()==4
        assert db.execute(sa.text('SELECT COUNT(*) FROM inventory')).scalar_one()==1
    assert head(engine)=='0004_exploration_inventory'
    engine.dispose()


def test_resume_after_seed_preserves_existing_items_and_inventory(tmp_path):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'seeded.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0003_names_archive')
    insert_data(engine,3)
    with engine.connect() as db:
        command.upgrade(config_for(db),'0004_exploration_inventory')
    with engine.begin() as db:
        db.execute(sa.text("INSERT INTO grimoire VALUES (1,'기존 마법','지우면 안 되는 데이터',5,3)"))
        db.execute(sa.text("UPDATE item SET weight_grams=250, description='수정한 설명' WHERE id=1"))
        db.execute(sa.text("UPDATE map_farming_item SET weight=30 WHERE id=1"))
        db.execute(sa.text("UPDATE inventory SET slot_capacity=12,max_weight_grams=35000"))
        db.execute(sa.text("INSERT INTO inventory_entry (inventory_id,item_id,quantity) SELECT id,1,3 FROM inventory"))
        # Simulate a failed version write in an isolated test DB only.
        db.execute(sa.text("UPDATE alembic_version SET version_num='0003_names_archive'"))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0004_exploration_inventory')
        assert db.execute(sa.text('SELECT COUNT(*) FROM item')).scalar_one()==4
        assert db.execute(sa.text('SELECT COUNT(*) FROM farming_item')).scalar_one()==4
        assert db.execute(sa.text('SELECT COUNT(*) FROM map_farming_item')).scalar_one()==4
        assert db.execute(sa.text('SELECT COUNT(*) FROM inventory')).scalar_one()==1
        assert db.execute(sa.text('SELECT quantity FROM inventory_entry')).scalar_one()==3
        assert tuple(db.execute(sa.text('SELECT slot_capacity,max_weight_grams FROM inventory')).one())==(12,35000)
        assert db.execute(sa.text('SELECT weight_grams FROM item WHERE id=1')).scalar_one()==250
        assert db.execute(sa.text('SELECT description FROM item WHERE id=1')).scalar_one()=='수정한 설명'
        assert db.execute(sa.text('SELECT weight FROM map_farming_item WHERE id=1')).scalar_one()==30
        assert db.execute(sa.text('SELECT magic_name FROM grimoire')).scalar_one()=='기존 마법'
    engine.dispose()


def test_wrong_existing_schema_stops_without_deleting_data(tmp_path):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    engine=sa.create_engine('sqlite:///'+str(tmp_path/'wrong.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db),'0003_names_archive')
    with engine.begin() as db:
        db.execute(sa.text('CREATE TABLE grimoire (id INTEGER PRIMARY KEY, custom_name TEXT)'))
        db.execute(sa.text("INSERT INTO grimoire VALUES (1,'보존')"))
    with engine.connect() as db:
        with pytest.raises(RuntimeError,match='grimoire 기존 구조가 달라'):
            command.upgrade(config_for(db),'0004_exploration_inventory')
    with engine.connect() as db:
        assert db.execute(sa.text('SELECT custom_name FROM grimoire')).scalar_one()=='보존'
    assert head(engine)=='0003_names_archive'
    engine.dispose()
