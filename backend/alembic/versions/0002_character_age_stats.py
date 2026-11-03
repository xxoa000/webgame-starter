"""나이 컬럼과 기본 스탯 합계 20. 이전 v2 적용 DB도 안전하게 편입."""
import secrets
from alembic import op
import sqlalchemy as sa

revision = '0002_age_stats'
down_revision = '0001_initial'
branch_labels = None
depends_on = None
CORE_STATS = ('strength','stamina','intelligence','agility','luck')


def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    connection = op.get_bind()
    columns = {column['name'] for column in sa.inspect(connection).get_columns('character')}
    if 'age' not in columns:
        op.add_column('character', sa.Column('age', sa.Integer(), nullable=True))
    table = sa.table('character', sa.column('id', sa.Integer()), sa.column('stats', sa.JSON()))
    changed = 0
    for row in connection.execute(sa.select(table)).mappings():
        stats = row['stats']
        if not isinstance(stats, dict):
            raise RuntimeError(f"캐릭터 {row['id']}의 stats가 JSON 객체가 아니야.")
        valid = (all(type(stats.get(key)) is int and 1 <= stats[key] <= 16 for key in CORE_STATS)
                 and sum(stats[key] for key in CORE_STATS) == 20)
        if not valid:
            cuts = [0, *sorted(secrets.SystemRandom().sample(range(1, 20), 4)), 20]
            normalized = {**stats, **{key: cuts[i+1]-cuts[i] for i,key in enumerate(CORE_STATS)}}
            connection.execute(table.update().where(table.c.id == row['id']).values(stats=normalized))
            changed += 1
    print(f'기본 스탯 합계 20 변환: {changed}명. 기존 외모·키·나이·재추첨 횟수 유지.')


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError('기본 스탯 재분배를 되돌릴 수 없어. 이전 데이터는 백업에서 복원해.')
