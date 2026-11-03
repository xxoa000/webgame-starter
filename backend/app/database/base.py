"""모든 테이블의 생성·수정 시각과 공통 SQLAlchemy 기반을 정의한다."""
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """시간대 없는 UTC 시각을 반환한다."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UpdatedTimeDefault(FunctionElement):
    """DB 종류에 맞는 수정 시각 기본식을 표현한다."""
    inherit_cache = True


@compiles(UpdatedTimeDefault)
def compile_updated_time(element, compiler, **kwargs):
    """SQLite 등에서 사용할 기본 시각 식을 생성한다."""
    return 'CURRENT_TIMESTAMP'


@compiles(UpdatedTimeDefault, 'mysql')
def compile_mysql_updated_time(element, compiler, **kwargs):
    """MySQL 직접 수정에도 동작하는 자동 갱신 식을 생성한다."""
    return 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'


class Base(DeclarativeBase):
    """공통 감사 시각을 모든 애플리케이션 모델에 상속한다."""
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
        default=utc_now, server_default=func.current_timestamp(), comment='생성 시각(UTC)')
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False,
        default=utc_now, onupdate=utc_now, server_default=UpdatedTimeDefault(), comment='마지막 수정 시각(UTC)')
