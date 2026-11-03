"""One-time upgrade: python -m app.migrate_character_v2. Back up the DB first."""
from sqlalchemy import inspect, text, select, Table, MetaData
from .db import engine, SessionLocal
from .config import CORE_STATS
from .modules.characters.stats import roll


def main():
    columns = {column['name'] for column in inspect(engine).get_columns('character')}
    if 'age' not in columns:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE `character` ADD COLUMN age INTEGER NULL'))
        print('age 컬럼 추가 완료')
    changed = 0
    table = Table("character", MetaData(), autoload_with=engine)
    with SessionLocal() as db:
        for character in db.execute(select(table).with_for_update()).mappings():
            stats = character["stats"]
            valid = (all(type(stats.get(key)) is int and 1 <= stats[key] <= 16 for key in CORE_STATS)
                     and sum(stats[key] for key in CORE_STATS) == 20)
            if not valid:
                generated = roll()
                db.execute(table.update().where(table.c.id == character["id"]).values(
                    stats={**stats, **{key: generated[key] for key in CORE_STATS}}))
                changed += 1
        db.commit()
    print(f'기본 스탯 변환: {changed}명. 외모·키·재추첨 횟수는 유지. 기존 나이는 미설정(NULL).')


if __name__ == '__main__':
    main()
