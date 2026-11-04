"""공유 균열 이벤트·개인 기여·전용 물자 발견을 보존한다."""
from alembic import op
import sqlalchemy as sa

revision = '0018_shared_raids'
down_revision = '0017_shop_upgrades'
branch_labels = None
depends_on = None


def audit():
    """모든 신규 테이블에 DB별 감사 시각을 추가한다."""
    updated = 'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP' if op.get_bind().dialect.name == 'mysql' else 'CURRENT_TIMESTAMP'
    return [sa.Column('create_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'), comment='생성 시각(UTC)'),
            sa.Column('update_at', sa.DateTime(), nullable=False, server_default=sa.text(updated), comment='마지막 수정 시각(UTC)')]


def upgrade():
    """기존 게임 데이터는 보존하고 빈 이벤트 기록을 추가한다."""
    cycle = op.create_table('raid_cycle',
        sa.Column('id', sa.Integer(), primary_key=True, comment='전역 일정 잠금 ID'),
        sa.Column('next_at', sa.DateTime(), nullable=False, comment='다음 이벤트 시작 가능 시각(UTC)'), *audit())
    op.execute(cycle.insert().values(id=1, next_at=sa.func.current_timestamp()))
    op.create_table('raid_event',
        sa.Column('id', sa.Integer(), primary_key=True, comment='균열 이벤트 ID'),
        sa.Column('map_id', sa.Integer(), sa.ForeignKey('map.id'), nullable=False, comment='이벤트 지역'),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('item.id'), nullable=False, comment='이벤트 전용 물자'),
        sa.Column('status', sa.String(16), nullable=False, comment='수집·보스·종료 단계'),
        sa.Column('collected', sa.Integer(), nullable=False, comment='지역 전체 누적 회수량'),
        sa.Column('threshold', sa.Integer(), nullable=False, comment='보스 등장에 필요한 회수량'),
        sa.Column('boss_hp', sa.Integer(), nullable=False, comment='공유 보스 현재 HP'),
        sa.Column('boss_max_hp', sa.Integer(), nullable=False, comment='보스 최대 HP'),
        sa.Column('version', sa.Integer(), nullable=False, comment='공유 상태 버전'),
        sa.Column('closed_at', sa.DateTime(), nullable=True, comment='종료·정산 시각(UTC)'),
        sa.CheckConstraint("status IN ('collecting','boss','closed')", name='ck_raid_status'),
        sa.CheckConstraint('collected >= 0 AND threshold > 0 AND boss_hp >= 0 AND boss_hp <= boss_max_hp AND boss_max_hp > 0 AND version > 0', name='ck_raid_counters'), *audit())
    op.create_table('raid_member',
        sa.Column('id', sa.Integer(), primary_key=True, comment='기여 기록 ID'),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('raid_event.id'), nullable=False, comment='균열 이벤트 ID'),
        sa.Column('character_id', sa.Integer(), sa.ForeignKey('character.id', ondelete='SET NULL'), nullable=True, comment='참가 캐릭터'),
        sa.Column('name', sa.String(24), nullable=False, comment='참가 당시 이름'),
        sa.Column('items', sa.Integer(), nullable=False, comment='회수해 보관 중인 물자 수'),
        sa.Column('damage', sa.Integer(), nullable=False, comment='실제 누적 피해량'),
        sa.Column('reward', sa.Integer(), nullable=False, comment='지급한 스탯 포인트'),
        sa.UniqueConstraint('event_id', 'character_id', name='uq_raid_member'),
        sa.CheckConstraint('items >= 0 AND damage >= 0 AND reward >= 0', name='ck_raid_member_counters'), *audit())
    with op.batch_alter_table('exploration') as batch:
        batch.add_column(sa.Column('pending_raid_id', sa.Integer(), nullable=True, comment='발견한 물자의 소속 균열'))
        batch.create_foreign_key('fk_exploration_pending_raid', 'raid_event', ['pending_raid_id'], ['id'])


def downgrade():
    """지급된 보상과 기여 기록의 유실을 막는다."""
    raise RuntimeError('레이드 보상과 기여 기록 보존을 위해 자동 downgrade를 지원하지 않아.')
