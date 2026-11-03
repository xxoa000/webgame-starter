"""활성 이름 유일성과 삭제 이력. 이전 v3 적용 DB도 편입."""
from collections import defaultdict
import hashlib
import unicodedata
from alembic import op
import sqlalchemy as sa

revision = '0003_names_archive'
down_revision = '0002_age_stats'
branch_labels = None
depends_on = None


def canonical_key(value):
    """마이그레이션 대상의 기존 구조와 데이터를 확인하고 반영한다."""
    return hashlib.sha256(unicodedata.normalize('NFC', value.strip()).casefold().encode('utf-8')).hexdigest()


def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    connection = op.get_bind()
    table = sa.table('character', sa.column('id', sa.Integer()), sa.column('name', sa.String(24)), sa.column('status', sa.String(12)))
    rows = connection.execute(sa.select(table)).mappings().all()
    groups = defaultdict(list)
    invalid = []
    for row in rows:
        if row['status'] == 'ready':
            if not row['name'].strip():
                invalid.append(row['id'])
            groups[canonical_key(row['name'])].append(row['id'])
    duplicates = [ids for ids in groups.values() if len(ids) > 1]
    if duplicates or invalid:
        raise RuntimeError(f'이름을 정리한 뒤 다시 실행해. 중복 캐릭터 ID: {duplicates}, 빈 이름 ID: {invalid}')
    inspector = sa.inspect(connection)
    if 'name_key' not in {column['name'] for column in inspector.get_columns('character')}:
        op.add_column('character', sa.Column('name_key', sa.String(64), nullable=True))
    keyed = sa.table('character', sa.column('id', sa.Integer()), sa.column('name_key', sa.String(64)))
    for row in rows:
        connection.execute(keyed.update().where(keyed.c.id == row['id']).values(
            name_key=canonical_key(row['name']) if row['status'] == 'ready' else None))
    inspector = sa.inspect(connection)
    uniques = [set(item['column_names']) for item in inspector.get_unique_constraints('character')]
    uniques += [set(item['column_names']) for item in inspector.get_indexes('character') if item.get('unique')]
    if {'name_key'} not in uniques:
        # batch handles SQLite ALTER limitations; MySQL uses ALTER TABLE.
        frozen = None
        if connection.dialect.name == 'sqlite':
            frozen = sa.Table('character', sa.MetaData(), autoload_with=connection)
            # SQLite batch rebuild must retain legacy unnamed CHECK constraints.
            checks = sorted((item for item in frozen.constraints if isinstance(item, sa.CheckConstraint)),
                            key=lambda item: str(item.sqltext))
            for index, constraint in enumerate(checks):
                if constraint.name is None:
                    constraint.name = f'ck_character_legacy_{index}'
        with op.batch_alter_table('character', copy_from=frozen) as batch:
            batch.create_unique_constraint('uq_character_name_key', ['name_key'])
    if 'deleted_character' not in sa.inspect(connection).get_table_names():
        op.create_table('deleted_character',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('original_character_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('client.id'), nullable=False),
            sa.Column('name', sa.String(24), nullable=False),
            sa.Column('gender', sa.String(12), nullable=False),
            sa.Column('age', sa.Integer(), nullable=True),
            sa.Column('bio', sa.String(500), nullable=False),
            sa.Column('stats', sa.JSON(), nullable=False),
            sa.Column('rerolls', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(12), nullable=False),
            sa.Column('deleted_at', sa.DateTime(), nullable=False))
        op.create_index('ix_deleted_character_user_id', 'deleted_character', ['user_id'])
    else:
        required = {'id','original_character_id','user_id','name','gender','age','bio','stats','rerolls','status','deleted_at'}
        actual = {column['name'] for column in sa.inspect(connection).get_columns('deleted_character')}
        if required - actual:
            raise RuntimeError(f'삭제 이력 테이블 구조 확인이 필요해. 누락 컬럼: {sorted(required-actual)}')


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError('삭제 이력 보존을 위해 초기 편입 revision의 자동 downgrade는 지원하지 않아.')
