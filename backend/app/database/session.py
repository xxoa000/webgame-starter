"""DB 연결과 요청별 세션 수명을 관리한다."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from ..core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {})
@event.listens_for(engine, 'connect')
def set_connection_timezone(dbapi_connection, connection_record):
    """MySQL 연결의 감사 시각을 UTC로 고정한다."""
    if engine.dialect.name == 'mysql':
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")


SessionLocal = sessionmaker(engine, expire_on_commit=False)

def get_db():
    """요청 단위 DB 세션을 제공하고 종료한다."""
    with SessionLocal() as db:
        yield db
