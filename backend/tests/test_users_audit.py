"""감사 컬럼·사용자 이름 변경·권한 기본값·스키마 재실행 보존을 검증한다."""
import importlib.util
from pathlib import Path
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from alembic import command
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from test_alembic import config_for
from app.database.metadata import target_metadata
from app.modules.users.models import User


def test_migration_preserves_accounts_and_all_tables(tmp_path):
    """구 테이블을 전환한 뒤 재실행해도 상태와 감사 시각을 보존한다."""
    engine = sa.create_engine('sqlite:///' + str(tmp_path/'audit.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db), '0008_combat')
        before_tables = set(sa.inspect(db).get_table_names())
    with engine.begin() as db:
        db.execute(sa.text("INSERT INTO client (id,username,password_hash) VALUES (77,'preserved','same-hash')"))
        db.execute(sa.text("INSERT INTO login_session(token_hash,user_id,expires_at) VALUES (:token,77,:expires)"), {'token':'f'*64,'expires':datetime(2030,1,1)})
    with engine.connect() as db:
        # 감사 변경 자체의 보존·재실행을 검사한다. JWT 전환은 별도 테스트한다.
        command.upgrade(config_for(db), '0009_users_audit')
    with engine.begin() as db:
        inspector = sa.inspect(db)
        assert 'client' not in inspector.get_table_names()
        assert set(inspector.get_table_names()) == (before_tables - {'client'}) | {'users'}
        for table in inspector.get_table_names():
            columns = {column['name']: column for column in inspector.get_columns(table)}
            assert not columns['create_at']['nullable'] and not columns['update_at']['nullable']
        row = db.execute(sa.text('SELECT password_hash,user_status,auth,last_login_at,create_at FROM users WHERE id=77')).one()
        assert row[:4] == ('same-hash',1,0,None)
        assert inspector.get_foreign_keys('login_session')[0]['referred_table'] == 'users'
        db.execute(sa.text('UPDATE users SET user_status=2,auth=9 WHERE id=77'))
        spec = importlib.util.spec_from_file_location('users_audit_revision', Path(__file__).resolve().parents[1]/'alembic/versions/0009_users_audit.py')
        revision = importlib.util.module_from_spec(spec); spec.loader.exec_module(revision)
        with Operations.context(MigrationContext.configure(db)):
            revision.upgrade()
        after = db.execute(sa.text('SELECT user_status,auth,create_at FROM users WHERE id=77')).one()
        assert after == (2,9,row[4])
        assert db.execute(sa.text('SELECT COUNT(*) FROM login_session')).scalar_one() == 1
    engine.dispose()


def test_models_have_comments_and_mysql_update_defaults():
    """모든 컬럼 설명과 MySQL 자동 시각 갱신 DDL을 검증한다."""
    for table in target_metadata.tables.values():
        assert all(column.comment for column in table.columns), table.name
        ddl = str(sa.schema.CreateTable(table).compile(dialect=mysql.dialect()))
        assert 'ON UPDATE CURRENT_TIMESTAMP' in ddl
        assert 'COMMENT' in ddl
    ddl = str(sa.schema.CreateTable(User.__table__).compile(dialect=mysql.dialect()))
    assert 'user_status TINYINT' in ddl and 'auth TINYINT' in ddl


def test_mysql_comment_ddl_preserves_defaults_and_autoincrement():
    """COMMENT 변경이 기존 숫자·문자 기본값과 자동 증가를 보존하는 DDL인지 검사한다."""
    from io import StringIO
    output = StringIO()
    context = MigrationContext.configure(dialect_name='mysql', opts={'as_sql':True,'output_buffer':output})
    operation = Operations(context)
    operation.alter_column('sample', 'counter', existing_type=sa.Integer(), existing_nullable=False,
        existing_server_default=sa.text('10'), comment='수량')
    operation.alter_column('sample', 'state', existing_type=sa.String(12), existing_nullable=False,
        existing_server_default=sa.text("'active'"), comment='상태')
    operation.alter_column('sample', 'id', existing_type=sa.Integer(), existing_nullable=False,
        existing_server_default=None, autoincrement=True, comment='ID')
    ddl = output.getvalue()
    assert 'DEFAULT 10' in ddl and "DEFAULT 'active'" in ddl
    assert 'AUTO_INCREMENT' in ddl and "COMMENT '수량'" in ddl
