"""실행 전에 DB가 최신 revision인지 확인한다. 스키마를 자동 변경하지 않는다."""
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from .session import engine


def assert_schema_current():
    """현재 DB 리비전이 코드의 최신 리비전과 일치하는지 검사한다."""
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    expected = set(ScriptDirectory.from_config(config).get_heads())
    with engine.connect() as connection:
        current = set(MigrationContext.configure(connection).get_current_heads())
    if current != expected:
        raise RuntimeError("DB 마이그레이션이 필요해. backend 환경에서 alembic upgrade head를 실행해.")
