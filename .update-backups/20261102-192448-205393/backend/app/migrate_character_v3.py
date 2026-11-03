"""Stop application writers and back up MySQL before running this migration."""
from collections import defaultdict
from sqlalchemy import inspect, text
from .db import engine
from .models import DeletedCharacter
from .names import clean_name, name_key


def main():
    # Preflight before DDL: never silently rename/delete pre-existing duplicates.
    with engine.connect() as connection:
        rows = connection.execute(text('SELECT id, name, status FROM `character`')).mappings().all()
    groups = defaultdict(list)
    invalid = []
    for row in rows:
        if row['status'] == 'ready':
            if not clean_name(row['name']):
                invalid.append(row['id'])
            groups[name_key(row['name'])].append(row['id'])
    duplicates = [ids for ids in groups.values() if len(ids) > 1]
    if duplicates or invalid:
        raise SystemExit(f'마이그레이션 중단. 중복 이름 캐릭터 ID: {duplicates}, 빈 이름 ID: {invalid}. 기존 이름을 정리한 뒤 다시 실행해.')
    inspector = inspect(engine)
    columns = {column['name'] for column in inspector.get_columns('character')}
    if 'age' not in columns:
        raise SystemExit('먼저 python -m app.migrate_character_v2 실행이 필요해.')
    if 'name_key' not in columns:
        with engine.begin() as connection:
            connection.execute(text('ALTER TABLE `character` ADD COLUMN name_key VARCHAR(64) NULL'))
    with engine.begin() as connection:
        for row in rows:
            connection.execute(text('UPDATE `character` SET name_key=:key WHERE id=:id'),
                {'id': row['id'], 'key': name_key(row['name']) if row['status'] == 'ready' else None})
    inspector = inspect(engine)
    unique_columns = [set(item['column_names']) for item in inspector.get_unique_constraints('character')]
    unique_columns += [set(item['column_names']) for item in inspector.get_indexes('character') if item.get('unique')]
    if {'name_key'} not in unique_columns:
        with engine.begin() as connection:
            connection.execute(text('CREATE UNIQUE INDEX uq_character_name_key ON `character` (name_key)'))
    DeletedCharacter.__table__.create(engine, checkfirst=True)
    print('완료: 활성 캐릭터 이름 중복 방지 + deleted_character 삭제 이력 테이블')


if __name__ == '__main__':
    main()
