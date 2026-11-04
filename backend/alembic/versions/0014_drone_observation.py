"""탐색 위치를 보존하고 계정별 온라인 탐사 접속 신호를 저장한다."""
from alembic import op
import sqlalchemy as sa

revision = '0014_drone_observation'
down_revision = '0013_script_display'
branch_labels = None
depends_on = None


def upgrade():
    """기존 탐색 결과를 유지하며 위치와 온라인 집계 구조를 추가한다."""
    op.add_column('exploration', sa.Column('position_step', sa.Integer(), server_default='0', nullable=False, comment='성공한 탐색 이동 횟수, 재접속 시 위치 복원'))
    updated_default = 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' if op.get_bind().dialect.name == 'mysql' else 'CURRENT_TIMESTAMP'
    op.create_table('exploration_presence',
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, comment='접속 사용자 ID, 계정당 한 행'),
        sa.Column('map_id', sa.Integer(), sa.ForeignKey('map.id'), nullable=False, comment='현재 탐사 중인 맵 ID'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False, comment='마지막 탐색 화면 접속 신호(UTC)'),
        sa.Column('create_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='생성 시각(UTC)'),
        sa.Column('update_at', sa.DateTime(), server_default=sa.text(updated_default), nullable=False, comment='마지막 수정 시각(UTC)'))
    op.create_index('ix_presence_map_seen', 'exploration_presence', ['map_id', 'last_seen_at'])


def downgrade():
    """온라인 접속 정보와 새 위치 필드만 제거한다."""
    op.drop_index('ix_presence_map_seen', table_name='exploration_presence')
    op.drop_table('exploration_presence')
    op.drop_column('exploration', 'position_step')
