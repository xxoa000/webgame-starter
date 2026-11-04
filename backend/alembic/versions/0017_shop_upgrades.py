"""영구 확장 상품·미분배 스탯·식음료 및 이벤트 물품 표시를 추가한다."""
from alembic import op
import sqlalchemy as sa
revision = '0017_shop_upgrades'
down_revision = '0016_jwt_auth'
branch_labels = None
depends_on = None


def upgrade():
    """기존 잔액·물품·능력치는 보존하고 신규 기능의 기본값만 추가한다."""
    with op.batch_alter_table('character') as batch:
        batch.add_column(sa.Column('stat_points', sa.Integer(), nullable=False, server_default='0', comment='미분배 스탯 포인트'))
        batch.add_column(sa.Column('stat_version', sa.Integer(), nullable=False, server_default='0', comment='스탯 분배 변경 버전'))
        batch.create_check_constraint('ck_character_stat_points', 'stat_points >= 0 AND stat_version >= 0')
    with op.batch_alter_table('item') as batch:
        batch.add_column(sa.Column('edible', sa.Boolean(), nullable=False, server_default='0', comment='섭취 가능한 식음료 여부'))
        batch.add_column(sa.Column('is_event', sa.Boolean(), nullable=False, server_default='0', comment='이벤트 전용 아이템 여부'))
    updated = 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' if op.get_bind().dialect.name == 'mysql' else 'CURRENT_TIMESTAMP'
    table = op.create_table('shop_upgrade',
        sa.Column('code', sa.String(32), primary_key=True, comment='영구 상품 코드'),
        sa.Column('name', sa.String(80), nullable=False, comment='상품 이름'),
        sa.Column('description', sa.String(200), nullable=False, comment='상품 효과 안내'),
        sa.Column('price', sa.Integer(), nullable=False, comment='개당 구매 가격(C)'),
        sa.Column('create_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='생성 시각(UTC)'),
        sa.Column('update_at', sa.DateTime(), nullable=False, server_default=sa.text(updated), comment='마지막 수정 시각(UTC)'),
        sa.CheckConstraint('price > 0', name='ck_shop_upgrade_price'))
    op.bulk_insert(table, [
        {'code': 'bag_expansion', 'name': '가방 확장', 'description': '인벤토리 +1칸 · 최대 무게 +10kg', 'price': 1000},
        {'code': 'stat_point', 'name': '스탯 포인트 +1', 'description': '캐릭터 창에서 분배하는 스탯 포인트', 'price': 1000},
    ])
    op.execute(sa.text("UPDATE item SET edible=1 WHERE name IN ('밀봉 생수','통조림 식량')"))


def downgrade():
    """구매한 영구 효과의 실수 제거를 막기 위해 자동 역변환은 허용하지 않는다."""
    raise RuntimeError('구매한 용량과 포인트를 보존하기 위해 자동 downgrade를 지원하지 않아.')
