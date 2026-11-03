"""사용자 상태·권한·마지막 로그인 시각과 로그인 세션을 저장한다."""
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, CheckConstraint, SmallInteger
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class User(Base):
    """이용 상태와 권한을 분리하여 사용자 계정을 저장한다."""
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint('user_status IN (0,1,2,3)', name='ck_users_status'),
        CheckConstraint('auth IN (0,1,9)', name='ck_users_auth'),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment='사용자 ID')
    username: Mapped[str] = mapped_column(String(24), unique=True, comment='로그인 아이디')
    password_hash: Mapped[str] = mapped_column(String(255), comment='비밀번호 해시')
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='마지막 로그인 시각(UTC)')
    user_status: Mapped[int] = mapped_column(SmallInteger().with_variant(TINYINT(), 'mysql'),
        default=1, server_default='1', comment='계정 상태: 0휴면 1활성 2제재 3탈퇴')
    auth: Mapped[int] = mapped_column(SmallInteger().with_variant(TINYINT(), 'mysql'),
        default=0, server_default='0', comment='권한: 0USER 1STAFF 9ADMIN')


class LoginSession(Base):
    """원본 토큰 대신 해시와 만료 시각을 보관한다."""
    __tablename__ = 'login_session'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True, comment='세션 토큰 해시')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True, comment='사용자 ID')
    expires_at: Mapped[datetime] = mapped_column(DateTime, comment='세션 만료 시각(UTC)')
