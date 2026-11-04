"""대사 편집 뷰와 visibility 제거 시 원문 보존을 검증한다."""
import importlib.util
from pathlib import Path
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from test_flow import client


def test_script_display_view_preserves_content(client):
    """새 스키마에 편집 뷰를 만들고 키워드 이름과 원문을 조회한다."""
    _, factory = client
    spec = importlib.util.spec_from_file_location('display_revision', Path(__file__).resolve().parents[1] / 'alembic/versions/0013_script_display.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with factory() as db:
        db.execute(sa.text(module.VIEW_SQL))
        row = db.execute(sa.text("SELECT keyword_name FROM game_script_keyword_view WHERE code='found_K1_1'")).one()
        assert row[0] == '소심함'
        assert 'visibility' not in {column['name'] for column in sa.inspect(db.connection()).get_columns('game_script')}
        db.execute(sa.text("UPDATE game_script SET content='수동 편집 원문' WHERE code='found_K1_1'"))
        with Operations.context(MigrationContext.configure(db.connection())):
            module.downgrade()
            module.upgrade()
        assert db.execute(sa.text("SELECT content FROM game_script WHERE code='found_K1_1'")).scalar_one() == '수동 편집 원문'
        assert db.execute(sa.text("SELECT keyword_name FROM game_script_keyword_view WHERE code='found_K1_1'")).scalar_one() == '소심함'
