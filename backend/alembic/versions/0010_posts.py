"""게시판과 공지를 위한 posts 테이블을 생성한다."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import TINYINT

revision = '0010_posts'
down_revision = '0009_users_audit'
branch_labels = None
depends_on = None


def upgrade():
    """계정 생성이나 임의 공지 작성 없이 게시판 저장 구조만 추가한다."""
    db = op.get_bind()
    if 'posts' in sa.inspect(db).get_table_names():
        required = {'id','title','content','username','is_notice','post_status','create_at','update_at'}
        if not required.issubset({c['name'] for c in sa.inspect(db).get_columns('posts')}):
            raise RuntimeError('기존 posts 구조가 예상과 다릅니다.')
        indexes = {index['name'] for index in sa.inspect(db).get_indexes('posts')}
        if 'ix_posts_username' not in indexes:
            op.create_index('ix_posts_username', 'posts', ['username'])
        if 'ix_posts_listing' not in indexes:
            op.create_index('ix_posts_listing', 'posts', ['post_status','is_notice','create_at','id'])
        return
    op.create_table('posts',
        sa.Column('id', sa.Integer(), primary_key=True, comment='게시글 ID'),
        sa.Column('title', sa.String(200), nullable=False, comment='게시글 제목'),
        sa.Column('content', sa.Text(), nullable=False, comment='게시글 본문'),
        sa.Column('username', sa.String(24), nullable=False, comment='작성자 로그인 아이디'),
        sa.Column('is_notice', sa.SmallInteger().with_variant(TINYINT(), 'mysql'), nullable=False, server_default='0', comment='공지 여부: 0일반 1공지'),
        sa.Column('post_status', sa.SmallInteger().with_variant(TINYINT(), 'mysql'), nullable=False, server_default='1', comment='글 상태: 0숨김 1활성 2제재 3삭제'),
        sa.Column('create_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='생성 시각(UTC)'),
        sa.Column('update_at', sa.DateTime(), nullable=False,
            server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP'), comment='마지막 수정 시각(UTC)'),
        sa.CheckConstraint('is_notice IN (0,1)', name='ck_posts_notice'),
        sa.CheckConstraint('post_status IN (0,1,2,3)', name='ck_posts_status'))
    op.create_index('ix_posts_username', 'posts', ['username'])
    op.create_index('ix_posts_listing', 'posts', ['post_status','is_notice','create_at','id'])


def downgrade():
    """게시글 데이터 유실을 방지한다."""
    raise RuntimeError('게시글 보존을 위해 자동 downgrade는 지원하지 않습니다.')
