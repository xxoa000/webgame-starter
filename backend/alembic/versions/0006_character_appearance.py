"""피계약자와 삭제 보관함에 외형 JSON을 추가한다. 기존 성별·스탯·자원은 변경하지 않는다."""
from alembic import op
import sqlalchemy as sa

revision = "0006_character_appearance"
down_revision = "0005_vitals_encyclopedia"
branch_labels = None
depends_on = None


def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    connection = op.get_bind()
    for table in ("character", "deleted_character"):
        columns = {column["name"]: column for column in sa.inspect(connection).get_columns(table)}
        if "appearance" not in columns:
            op.add_column(table, sa.Column("appearance", sa.JSON(), nullable=True))
        elif not isinstance(columns["appearance"]["type"], sa.JSON):
            raise RuntimeError(f"{table}.appearance 컬럼이 JSON 형식이 아닙니다.")


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError("저장된 외형을 보존하기 위해 자동 downgrade를 지원하지 않습니다.")
