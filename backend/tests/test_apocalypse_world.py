"""기존 파밍 기록 정리·신규 월드 구성·재실행 안전성과 캐릭터 보존을 검증한다."""
import importlib.util
from pathlib import Path
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from test_flow import client, auth, make_ready
from test_exploration import world


def test_replace_world_with_existing_records(world):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory, _ = world
    before = c.get('/me').json()['character']
    with factory() as db:
        db.execute(sa.text('PRAGMA foreign_keys=ON'))
        character_id = before['id']
        inventory_id = db.execute(sa.text('SELECT id FROM inventory WHERE character_id=:c'), {'c': character_id}).scalar_one()
        db.execute(sa.text('INSERT INTO inventory_entry (inventory_id,item_id,quantity) VALUES (:i,1,3)'), {'i': inventory_id})
        db.execute(sa.text("INSERT INTO encyclopedia (character_id,item_id,first_map_id,discovered_at) VALUES (:c,1,1,CURRENT_TIMESTAMP)"), {'c': character_id})
        db.execute(sa.text("INSERT INTO exploration (character_id,map_id,status,turn,version,pending_item_id,pending_quantity,history) VALUES (:c,1,'active',1,1,2,1,'[]')"), {'c': character_id})
        spec = importlib.util.spec_from_file_location('apocalypse', Path(__file__).resolve().parents[1]/'alembic/versions/0007_apocalypse_world.py')
        revision = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(revision)
        with Operations.context(MigrationContext.configure(db.connection())):
            revision.upgrade()
            revision.upgrade()
        db.commit()
        assert db.execute(sa.text('SELECT COUNT(*) FROM map')).scalar_one() == 8
        assert db.execute(sa.text('SELECT COUNT(*) FROM item')).scalar_one() == 24
        assert db.execute(sa.text('SELECT COUNT(*) FROM map_farming_item')).scalar_one() == 24
        for table in ['inventory_entry', 'encyclopedia', 'exploration']:
            assert db.execute(sa.text(f'SELECT COUNT(*) FROM {table}')).scalar_one() == 0
        assert db.execute(sa.text('SELECT COUNT(*) FROM inventory')).scalar_one() == 1
        assert db.execute(sa.text('PRAGMA foreign_key_check')).all() == []
        assert all(empty + sum(weight for _, weight in loot) == 100 for _, _, empty, loot in revision.MAPS)
    after = c.get('/me').json()['character']
    for key in ['id', 'name', 'gender', 'stats', 'appearance']:
        assert after[key] == before[key]
