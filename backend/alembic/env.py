"""DATABASE_URL은 앱 설정과 공유한다. ini에 비밀번호를 적지 않는다."""
from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool
from app.core.config import settings
from app.database.metadata import target_metadata

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)


def migrate(connection):
    """연결된 DB에서 마이그레이션을 실행한다."""
    if connection.dialect.name == "mysql":
        connection.exec_driver_sql("SET time_zone = '+00:00'")
        connection.commit()
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    # Adoption revisions inspect the live DB; don't emit misleading offline SQL.
    raise RuntimeError("기존 DB 구조를 검사하므로 실제 DB 연결로 upgrade head를 실행해.")
else:
    provided = config.attributes.get("connection")
    if provided is not None:
        migrate(provided)
    else:
        engine = create_engine(settings.database_url, poolclass=pool.NullPool)
        with engine.connect() as connection:
            migrate(connection)
        engine.dispose()
