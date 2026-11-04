"""빈사·구조 요청·무료 재화와 상점 가격을 추가한다."""
from alembic import op
import sqlalchemy as sa
revision='0015_rescue_shop'
down_revision='0014_drone_observation'
branch_labels=None
depends_on=None


def upgrade():
    """기존 캐릭터·대사를 보존하며 구조 및 거래 구조를 추가한다."""
    op.add_column('character',sa.Column('downed',sa.Boolean(),nullable=False,server_default='0',comment='빈사 상태 여부'))
    op.add_column('users',sa.Column('money',sa.Integer(),nullable=False,server_default='1000',comment='보유 무료 크레딧, 계정 단위'))
    with op.batch_alter_table('users') as batch:
        batch.create_check_constraint('ck_users_money','money >= 0')
    op.add_column('item',sa.Column('buy_price',sa.Integer(),nullable=False,server_default='0',comment='구매 가격, 0이면 상점 미판매'))
    op.add_column('item',sa.Column('sell_price',sa.Integer(),nullable=False,server_default='10',comment='판매 가격, 무료 크레딧'))
    with op.batch_alter_table('item') as batch:
        batch.create_check_constraint('ck_item_prices','buy_price >= 0 AND sell_price >= 0 AND (buy_price = 0 OR sell_price <= buy_price)')
    prices={'밀봉 생수':(50,15),'통조림 식량':(70,20),'멸균 붕대':(80,25),'소독제':(60,18),'응급 처치 키트':(180,60)}
    for name,(buy,sell) in prices.items():
        op.get_bind().execute(sa.text('UPDATE item SET buy_price=:buy,sell_price=:sell WHERE name=:name'),{'buy':buy,'sell':sell,'name':name})
    updated='CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' if op.get_bind().dialect.name=='mysql' else 'CURRENT_TIMESTAMP'
    op.create_table('rescue_request',
        sa.Column('id',sa.Integer(),primary_key=True,comment='구조 요청 ID'),
        sa.Column('character_id',sa.Integer(),sa.ForeignKey('character.id',ondelete='CASCADE'),nullable=False,unique=True,comment='구조 대상 캐릭터 ID'),
        sa.Column('map_id',sa.Integer(),sa.ForeignKey('map.id'),nullable=False,comment='구조 대상 맵 ID'),
        sa.Column('status',sa.String(12),nullable=False,comment='waiting대기 rescued구조 abandoned포기'),
        sa.Column('requested_at',sa.DateTime(),nullable=False,comment='구조 요청 시각(UTC)'),
        sa.Column('due_at',sa.DateTime(),nullable=False,comment='NPC 구조 도착 시각(UTC)'),
        sa.Column('helper_user_id',sa.Integer(),sa.ForeignKey('users.id'),nullable=True,comment='구조한 사용자 ID, NPC는 NULL'),
        sa.Column('create_at',sa.DateTime(),nullable=False,server_default=sa.text('CURRENT_TIMESTAMP'),comment='생성 시각(UTC)'),
        sa.Column('update_at',sa.DateTime(),nullable=False,server_default=sa.text(updated),comment='마지막 수정 시각(UTC)'),
        sa.CheckConstraint("status IN ('waiting','rescued','abandoned')",name='ck_rescue_status'))


def downgrade():
    """구조·거래 필드만 제거한다. 재화 잔액은 되돌리기 시 제거된다."""
    op.drop_table('rescue_request')
    with op.batch_alter_table('item') as batch:
        batch.drop_constraint('ck_item_prices',type_='check')
        batch.drop_column('buy_price');batch.drop_column('sell_price')
    with op.batch_alter_table('users') as batch:
        batch.drop_constraint('ck_users_money',type_='check')
        batch.drop_column('money')
    op.drop_column('character','downed')
