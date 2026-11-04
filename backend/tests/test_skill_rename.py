"""스킬 명칭 변경의 데이터 보존·중단 후 재실행·구조 충돌을 검증한다."""
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from test_alembic import config_for


def revision():
    """검증할 이름 변경 마이그레이션을 직접 불러온다."""
    file = Path(__file__).resolve().parents[1] / 'alembic/versions/0012_rename_magic_to_skill.py'
    spec = importlib.util.spec_from_file_location('skill_rename', file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_upgrade_downgrade_preserves_rows_and_timestamps(tmp_path):
    """왕복 변경과 반복 실행 뒤에도 ID·본문·능력치·감사 시각을 보존한다."""
    engine = sa.create_engine('sqlite:///' + str(tmp_path / 'rename.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db), '0011_personality_scripts')
        db.execute(sa.text("INSERT INTO grimoire(id,magic_name,description,power,mana_cost,create_at,update_at) VALUES(42,'기존 이름','본문 보존',7,3,'2025-01-02 03:04:05','2025-06-07 08:09:10')"))
        db.commit()
        original = db.execute(sa.text('SELECT * FROM grimoire')).one()
        command.upgrade(config_for(db), '0012_rename_magic_to_skill')
        db.commit()
        assert 'grimoire' not in sa.inspect(db).get_table_names()
        assert db.execute(sa.text('SELECT * FROM skill')).one() == original
        assert 'skill_name' in {column['name'] for column in sa.inspect(db).get_columns('skill')}
        module = revision()
        with Operations.context(MigrationContext.configure(db)):
            module.upgrade()
        assert db.execute(sa.text('SELECT * FROM skill')).one() == original
        with pytest.raises(sa.exc.IntegrityError):
            db.execute(sa.text("INSERT INTO skill(id,skill_name,description,power,mana_cost) VALUES(43,'잘못된 값','',-1,0)"))
        db.rollback()
        command.downgrade(config_for(db), '0011_personality_scripts')
        assert db.execute(sa.text('SELECT * FROM grimoire')).one() == original
        assert 'skill' not in sa.inspect(db).get_table_names()
    engine.dispose()


def test_partial_rename_resumes_without_recreating_table(tmp_path):
    """테이블 이름만 변경된 중단 상태에서 컬럼 이름 변경을 이어서 진행한다."""
    engine = sa.create_engine('sqlite:///' + str(tmp_path / 'partial.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db), '0011_personality_scripts')
        db.execute(sa.text("INSERT INTO grimoire(id,magic_name,description,power,mana_cost) VALUES(9,'중단 보존','본문',1,2)"))
        db.execute(sa.text('ALTER TABLE grimoire RENAME TO skill'))
        db.commit()
        command.upgrade(config_for(db), '0012_rename_magic_to_skill')
        db.commit()
        assert db.execute(sa.text('SELECT id,skill_name FROM skill')).one() == (9, '중단 보존')
    engine.dispose()


def test_conflicting_tables_fail_before_mutation(tmp_path):
    """두 테이블이 함께 있으면 어느 쪽도 삭제하거나 덮어쓰지 않는다."""
    engine = sa.create_engine('sqlite:///' + str(tmp_path / 'conflict.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db), '0011_personality_scripts')
        db.execute(sa.text('CREATE TABLE skill(id INTEGER PRIMARY KEY)'))
        db.execute(sa.text('INSERT INTO skill VALUES(99)'))
        db.commit()
        with pytest.raises(RuntimeError, match='모두 존재'):
            command.upgrade(config_for(db), '0012_rename_magic_to_skill')
        db.commit()
        assert {'grimoire', 'skill'} <= set(sa.inspect(db).get_table_names())
        assert db.execute(sa.text('SELECT id FROM skill')).scalar_one() == 99
    engine.dispose()


def test_mysql_emits_only_rename_and_comment_changes(monkeypatch):
    """MySQL용 SQL에서도 테이블 삭제·재생성이나 시각 기본식 변경이 없는지 확인한다."""
    from io import StringIO
    module = revision()
    class Inspector:
        """SQL 생성 검사에 필요한 기존 스키마 정보만 제공한다."""
        def get_table_names(self):
            """변경 전 테이블을 반환한다."""
            return ['grimoire']
        def get_columns(self, table):
            """원본 컬럼 이름을 반환한다."""
            return [{'name': name} for name in ('id', 'magic_name', 'description', 'power', 'mana_cost', 'create_at', 'update_at')]
    monkeypatch.setattr(module.sa, 'inspect', lambda connection: Inspector())
    output = StringIO()
    context = MigrationContext.configure(dialect_name='mysql', opts={'as_sql': True, 'output_buffer': output})
    with Operations.context(context):
        module.upgrade()
    sql = output.getvalue()
    assert 'RENAME' in sql and 'skill_name' in sql
    assert 'DROP TABLE' not in sql and 'CREATE TABLE' not in sql
    assert 'create_at' not in sql and 'update_at' not in sql
