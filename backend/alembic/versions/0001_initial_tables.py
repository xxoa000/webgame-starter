"""초기 테이블 생성 또는 기존 수동 관리 DB의 기본 구조 확인."""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def require_columns(table, required):
    """마이그레이션 대상의 기존 구조와 데이터를 확인하고 반영한다."""
    actual = {column['name'] for column in sa.inspect(op.get_bind()).get_columns(table)}
    missing = set(required) - actual
    if missing:
        raise RuntimeError(f'{table} 구조가 예상과 달라. 누락 컬럼: {sorted(missing)}')


def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    existing = set(sa.inspect(op.get_bind()).get_table_names())
    if 'client' not in existing:
        op.create_table('client',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('username', sa.String(24), nullable=False),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.UniqueConstraint('username'))
    else:
        require_columns('client', ['id', 'username', 'password_hash'])
    if 'login_session' not in existing:
        op.create_table('login_session',
            sa.Column('token_hash', sa.String(64), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('client.id'), nullable=False),
            sa.Column('expires_at', sa.DateTime(), nullable=False))
        op.create_index('ix_login_session_user_id', 'login_session', ['user_id'])
    else:
        require_columns('login_session', ['token_hash', 'user_id', 'expires_at'])
    if 'character' not in existing:
        op.create_table('character',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('client.id'), nullable=False),
            sa.Column('name', sa.String(24), nullable=False),
            sa.Column('gender', sa.String(12), nullable=False),
            sa.Column('bio', sa.String(500), nullable=False),
            sa.Column('stats', sa.JSON(), nullable=False),
            sa.Column('rerolls', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(12), nullable=False),
            sa.UniqueConstraint('user_id'),
            sa.CheckConstraint('rerolls >= 0 AND rerolls <= 10'),
            sa.CheckConstraint("gender IN ('male','female','other')"))
    else:
        require_columns('character', ['id','user_id','name','gender','bio','stats','rerolls','status'])


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError('기존 DB 편입 revision은 자동으로 테이블을 삭제하지 않아. 복원은 백업을 사용해.')
