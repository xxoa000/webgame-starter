"""대사 공개 여부를 layer로 통일하고 키워드 편집용 조회 뷰를 추가한다."""
from alembic import op
import sqlalchemy as sa

revision = '0013_script_display'
down_revision = '0012_rename_magic_to_skill'
branch_labels = None
depends_on = None

VIEW_SQL = '''CREATE VIEW game_script_keyword_view AS
SELECT s.id AS script_id, s.code, s.situation_code, s.action_code,
       s.layer, s.content, s.priority, s.weight, s.is_active,
       c.id AS condition_id, c.condition_group,
       k.id AS keyword_id, k.name AS keyword_name, k.category AS keyword_category,
       c.map_id, c.hp_min_percent, c.hp_max_percent
FROM game_script s
LEFT JOIN game_script_condition c ON c.script_id = s.id
LEFT JOIN personality_keyword k ON k.id = c.keyword_id'''


def upgrade():
    """본문과 조건 데이터를 보존하며 중복 컬럼을 제거하고 조회 뷰를 만든다."""
    with op.batch_alter_table('game_script') as batch:
        batch.drop_constraint('ck_script_visibility', type_='check')
        batch.drop_column('visibility')
    op.execute(VIEW_SQL)


def downgrade():
    """조회 뷰를 제거하고 layer 기준으로 기존 공개 여부를 복원한다."""
    op.execute('DROP VIEW game_script_keyword_view')
    op.add_column('game_script', sa.Column('visibility', sa.String(8), nullable=False, server_default='OWNER', comment='PUBLIC공개 OWNER소유자전용'))
    op.execute("UPDATE game_script SET visibility = CASE WHEN layer='SPEECH' THEN 'PUBLIC' ELSE 'OWNER' END")
    with op.batch_alter_table('game_script') as batch:
        batch.create_check_constraint('ck_script_visibility', "(layer='SPEECH' AND visibility='PUBLIC') OR (layer IN ('THOUGHT','NARRATION') AND visibility='OWNER')")
