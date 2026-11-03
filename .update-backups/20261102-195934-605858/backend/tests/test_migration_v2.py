from sqlalchemy import create_engine, text, select, Table, MetaData
from sqlalchemy.orm import sessionmaker
from app import migrate_character_v2 as migration


def test_v2_on_old_schema_without_name_key(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///'+str(tmp_path/'v2.db'))
    monkeypatch.setattr(migration, 'engine', engine)
    monkeypatch.setattr(migration, 'SessionLocal', sessionmaker(engine))
    with engine.begin() as db:
        db.execute(text('CREATE TABLE character (id INTEGER PRIMARY KEY, stats JSON)'))
        db.execute(text('INSERT INTO character VALUES (1, :stats)'), {'stats':'{"strength":50,"stamina":50,"intelligence":50,"agility":50,"luck":50,"appearance":80,"height_cm":170}'})
    migration.main()
    table = Table('character', MetaData(), autoload_with=engine)
    with engine.connect() as db:
        stats = db.execute(select(table.c.stats)).scalar_one()
        assert sum(stats[key] for key in migration.CORE_STATS) == 20
        assert stats['appearance'] == 80 and stats['height_cm'] == 170
    migration.main()
    with engine.connect() as db:
        assert stats == db.execute(select(table.c.stats)).scalar_one()
    engine.dispose()
