"""작성자 아이디·공지 여부·공개 상태를 포함한 게시글을 저장한다."""
from sqlalchemy import String, Text, SmallInteger, CheckConstraint, Index
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Post(Base):
    """일반 게시글과 공지를 같은 테이블로 관리한다."""
    __tablename__ = 'posts'
    __table_args__ = (
        CheckConstraint('is_notice IN (0,1)', name='ck_posts_notice'),
        CheckConstraint('post_status IN (0,1,2,3)', name='ck_posts_status'),
        Index('ix_posts_listing', 'post_status', 'is_notice', 'create_at', 'id'),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment='게시글 ID')
    title: Mapped[str] = mapped_column(String(200), comment='게시글 제목')
    content: Mapped[str] = mapped_column(Text, comment='게시글 본문')
    username: Mapped[str] = mapped_column(String(24), index=True, comment='작성자 로그인 아이디')
    is_notice: Mapped[int] = mapped_column(SmallInteger().with_variant(TINYINT(), 'mysql'), default=0, server_default='0', comment='공지 여부: 0일반 1공지')
    post_status: Mapped[int] = mapped_column(SmallInteger().with_variant(TINYINT(), 'mysql'), default=1, server_default='1', comment='글 상태: 0숨김 1활성 2제재 3삭제')
