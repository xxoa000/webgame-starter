"""기존 행과 감사 시각을 보존하면서 grimoire/magic_name을 skill/skill_name으로 바꾼다.

Revision ID: 0012_rename_magic_to_skill
Revises: 0011_personality_scripts
"""
from alembic import op
import sqlalchemy as sa

revision = '0012_rename_magic_to_skill'
down_revision = '0011_personality_scripts'
branch_labels = None
depends_on = None


def rename_skill_table(source, target, old_column, new_column, reverse=False):
    """구조를 먼저 검증하고 테이블·컬럼 이름만 변경해 데이터 손실을 방지한다."""
    connection = op.get_bind()
    tables = set(sa.inspect(connection).get_table_names())
    if source in tables and target in tables:
        raise RuntimeError(f'{source}와 {target}이 모두 존재해. 데이터를 확인한 뒤 이름 변경을 진행해.')
    table = source if source in tables else target
    if table not in tables:
        raise RuntimeError(f'{source} 또는 {target} 테이블이 필요해.')
    columns = {row['name'] for row in sa.inspect(connection).get_columns(table)}
    required = {'id', 'description', 'power', 'mana_cost', 'create_at', 'update_at'}
    if not required <= columns or ((old_column in columns) == (new_column in columns)):
        raise RuntimeError(f'{table} 기존 구조가 달라. 이름 변경 전에 컬럼을 확인해.')
    if table == source:
        op.rename_table(source, target)
    # MySQL의 DDL 중단 뒤 재실행해도 이미 바뀐 이름을 다시 바꾸지 않는다.
    mysql = connection.dialect.name in {'mysql', 'mariadb'}
    if old_column in columns:
        options = {'comment': '마법 이름' if reverse else '스킬 이름'} if mysql else {}
        op.alter_column(target, old_column, new_column_name=new_column,
                        existing_type=sa.String(100), existing_nullable=False, **options)
    if mysql:
        op.alter_column(target, 'power', existing_type=sa.Integer(), existing_nullable=False,
                        comment='마법 위력' if reverse else '스킬 위력')
    # create_at/update_at의 기존 기본식은 그대로 두므로 MySQL 자동 갱신도 유지된다.


def upgrade():
    """테이블을 재생성하지 않고 스킬 명칭으로 바꾼다."""
    rename_skill_table('grimoire', 'skill', 'magic_name', 'skill_name')


def downgrade():
    """기존 행을 유지하면서 이전 테이블·컬럼 이름으로 되돌린다."""
    rename_skill_table('skill', 'grimoire', 'skill_name', 'magic_name', reverse=True)
