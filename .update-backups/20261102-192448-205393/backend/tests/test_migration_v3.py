from sqlalchemy import create_engine, text, inspect
import pytest
from app import migrate_character_v3 as migration


def legacy_engine(path):
    engine = create_engine('sqlite:///'+str(path))
    with engine.begin() as db:
        db.execute(text('CREATE TABLE client (id INTEGER PRIMARY KEY)'))
        db.execute(text('CREATE TABLE character (id INTEGER PRIMARY KEY, name VARCHAR(24), status VARCHAR(12), age INTEGER)'))
    return engine


def test_migration_preserves_rows_and_is_repeatable(tmp_path, monkeypatch):
    engine=legacy_engine(tmp_path/'legacy.db')
    monkeypatch.setattr(migration, 'engine', engine)
    with engine.begin() as db:
        db.execute(text("INSERT INTO character VALUES (1, 'Alice', 'ready', 12), (2, '', 'draft', NULL), (3, '', 'draft', NULL)"))
    migration.main()
    migration.main()
    assert 'deleted_character' in inspect(engine).get_table_names()
    with engine.connect() as db:
        rows=db.execute(text('SELECT id, name, name_key FROM character ORDER BY id')).all()
        assert len(rows)==3 and rows[0].name=='Alice'
        assert rows[0].name_key is not None
        assert rows[1].name_key is None and rows[2].name_key is None
    engine.dispose()


def test_migration_stops_for_duplicate_names(tmp_path, monkeypatch):
    engine=legacy_engine(tmp_path/'duplicate.db')
    monkeypatch.setattr(migration, 'engine', engine)
    with engine.begin() as db:
        db.execute(text("INSERT INTO character VALUES (1, 'Alice', 'ready', 12), (2, 'ALICE', 'ready', 13)"))
    with pytest.raises(SystemExit, match='중복 이름'):
        migration.main()
    assert 'name_key' not in {x['name'] for x in inspect(engine).get_columns('character')}
    engine.dispose()
