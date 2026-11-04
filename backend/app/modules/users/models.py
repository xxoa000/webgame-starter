"""사용자 상태·권한·마지막 로그인 시각과 JWT 무효화 버전을 저장한다."""
from datetime import datetime
from sqlalchemy import String, DateTime, CheckConstraint, SmallInteger
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class User(Base):
    """이용 상태와 권한을 분리하여 사용자 계정을 저장한다."""
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint('token_version >= 0', name='ck_users_token_version'),
        CheckConstraint('money >= 0', name='ck_users_money'),
        CheckConstraint('user_status IN (0,1,2,3)', name='ck_users_status'),
        CheckConstraint('auth IN (0,1,9)', name='ck_users_auth'),
    )
    token_version: Mapped[int] = mapped_column(default=0, server_default='0', comment='JWT 무효화 버전, 로그아웃마다 증가')
    money: Mapped[int] = mapped_column(default=1000, server_default='1000', comment='보유 무료 크레딧, 계정 단위')
    id: Mapped[int] = mapped_column(primary_key=True, comment='사용자 ID')
    username: Mapped[str] = mapped_column(String(24), unique=True, comment='로그인 아이디')
    password_hash: Mapped[str] = mapped_column(String(255), comment='비밀번호 해시')
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment='마지막 로그인 시각(UTC)')
    user_status: Mapped[int] = mapped_column(SmallInteger().with_variant(TINYINT(), 'mysql'),
        default=1, server_default='1', comment='계정 상태: 0휴면 1활성 2제재 3탈퇴')
    auth: Mapped[int] = mapped_column(SmallInteger().with_variant(TINYINT(), 'mysql'),
        default=0, server_default='0', comment='권한: 0USER 1STAFF 9ADMIN')
