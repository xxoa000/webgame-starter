"""세션 테이블을 제거하고 사용자별 JWT 무효화 버전을 추가한다."""
from alembic import op
import sqlalchemy as sa
revision = '0016_jwt_auth'
down_revision = '0015_rescue_shop'
branch_labels = None
depends_on = None


def upgrade():
    """사용자·게임 데이터를 보존하고 기존 로그인 세션만 폐기한다."""
    with op.batch_alter_table('users') as batch:
        batch.add_column(sa.Column('token_version', sa.Integer(), nullable=False, server_default='0', comment='JWT 무효화 버전, 로그아웃마다 증가'))
        batch.create_check_constraint('ck_users_token_version', 'token_version >= 0')
    op.drop_table('login_session')


def downgrade():
    """빈 세션 테이블을 복구한다. 폐기된 토큰은 복원하지 않는다."""
    updated = 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' if op.get_bind().dialect.name == 'mysql' else 'CURRENT_TIMESTAMP'
    op.create_table('login_session',
        sa.Column('token_hash', sa.String(64), primary_key=True, comment='세션 토큰 해시'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, comment='사용자 ID'),
        sa.Column('expires_at', sa.DateTime(), nullable=False, comment='세션 만료 시각(UTC)'),
        sa.Column('create_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='생성 시각(UTC)'),
        sa.Column('update_at', sa.DateTime(), nullable=False, server_default=sa.text(updated), comment='마지막 수정 시각(UTC)'))
    op.create_index('ix_login_session_user_id', 'login_session', ['user_id'])
    with op.batch_alter_table('users') as batch:
        batch.drop_constraint('ck_users_token_version', type_='check')
        batch.drop_column('token_version')
