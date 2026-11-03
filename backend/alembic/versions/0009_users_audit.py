"""사용자 테이블명·상태·권한과 전체 테이블의 감사 시각·컬럼 설명을 추가한다."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import TINYINT

revision = '0009_users_audit'
down_revision = '0008_combat'
branch_labels = None
depends_on = None

COMMENTS = {'alembic_version': {'version_num': '적용된 마이그레이션 버전'},
 'character': {'age': '나이(세)',
               'appearance': '프로필 프리셋 정보',
               'bio': '프로필 소개',
               'gender': '성별',
               'hp_current': '현재 HP',
               'id': '고유 ID',
               'mp_current': '현재 MP',
               'name': '이름',
               'name_key': '이름 중복 검사 키',
               'rerolls': '남은 능력치 재추첨 횟수',
               'stamina_current': '현재 스태미나',
               'stamina_updated_at': '스태미나 회복 기준 시각(UTC)',
               'stats': '능력치 정보',
               'status': '진행 상태',
               'user_id': '사용자 ID'},
 'deleted_character': {'age': '나이(세)',
                       'appearance': '프로필 프리셋 정보',
                       'bio': '프로필 소개',
                       'deleted_at': '삭제 또는 사망 시각(UTC)',
                       'gender': '성별',
                       'id': '고유 ID',
                       'name': '이름',
                       'original_character_id': '원래 캐릭터 ID',
                       'rerolls': '남은 능력치 재추첨 횟수',
                       'stats': '능력치 정보',
                       'status': '진행 상태',
                       'user_id': '사용자 ID'},
 'drop_item': {'item_id': '아이템 ID'},
 'encyclopedia': {'character_id': '캐릭터 ID',
                  'discovered_at': '최초 발견 시각(UTC)',
                  'first_map_id': '최초 발견 맵 ID',
                  'id': '고유 ID',
                  'item_id': '아이템 ID'},
 'exploration': {'character_id': '캐릭터 ID',
                 'combat': '진행 중인 전투 상태',
                 'history': '최근 탐색 기록',
                 'id': '고유 ID',
                 'map_id': '맵 ID',
                 'pending_item_id': '회수 대기 아이템 ID',
                 'pending_quantity': '회수 대기 수량',
                 'status': '진행 상태',
                 'turn': '진행 턴 수',
                 'version': '동시 요청 검증 번호'},
 'farming_item': {'item_id': '아이템 ID'},
 'grimoire': {'description': '설명',
              'id': '고유 ID',
              'magic_name': '마법 이름',
              'mana_cost': '필요 MP',
              'power': '마법 위력'},
 'inventory': {'character_id': '캐릭터 ID',
               'id': '고유 ID',
               'max_weight_grams': '최대 수용 무게(g)',
               'slot_capacity': '최대 보관 종류 수'},
 'inventory_entry': {'id': '고유 ID', 'inventory_id': '인벤토리 ID', 'item_id': '아이템 ID', 'quantity': '보유 수량'},
 'item': {'description': '설명', 'id': '고유 ID', 'kind': '아이템 분류', 'name': '이름', 'weight_grams': '개당 무게(g)'},
 'login_session': {'expires_at': '세션 만료 시각(UTC)', 'token_hash': '세션 토큰 해시', 'user_id': '사용자 ID'},
 'map': {'description': '설명', 'empty_weight': '빈손 결과 추첨 가중치', 'id': '고유 ID', 'name': '이름'},
 'map_farming_item': {'farming_item_id': '파밍 아이템 ID', 'id': '고유 ID', 'map_id': '맵 ID', 'weight': '추첨 가중치'},
 'map_monster': {'id': '고유 ID', 'map_id': '맵 ID', 'monster_id': '몬스터 ID', 'weight': '추첨 가중치'},
 'monster': {'attack_max': '최대 공격력',
             'attack_min': '최소 공격력',
             'defense': '방어력',
             'description': '설명',
             'hp': '최대 HP',
             'id': '고유 ID',
             'name': '이름'},
 'monster_drop_item': {'drop_item_id': '전리품 아이템 ID',
                       'id': '고유 ID',
                       'monster_id': '몬스터 ID',
                       'weight': '추첨 가중치'},
 'posts': {'content': '게시글 본문',
           'id': '게시글 ID',
           'is_notice': '공지 여부: 0일반 1공지',
           'post_status': '글 상태: 0숨김 1활성 2제재 3삭제',
           'title': '게시글 제목',
           'username': '작성자 로그인 아이디'},
 'recipe': {'id': '고유 ID',
            'main_item_id': '주재료 아이템 ID',
            'name': '이름',
            'result_item_id': '조합 결과 아이템 ID',
            'sub_item1_id': '첫 번째 부재료 ID',
            'sub_item2_id': '두 번째 부재료 ID'},
 'users': {'auth': '권한: 0USER 1STAFF 9ADMIN',
           'id': '사용자 ID',
           'last_login_at': '마지막 로그인 시각(UTC)',
           'password_hash': '비밀번호 해시',
           'user_status': '계정 상태: 0휴면 1활성 2제재 3탈퇴',
           'username': '로그인 아이디'}}


def upgrade():
    """기존 계정과 연결 데이터를 유지하면서 공통 스키마를 확장한다."""
    db = op.get_bind()
    names = set(sa.inspect(db).get_table_names())
    if 'client' in names and 'users' in names:
        raise RuntimeError('client와 users가 동시에 있어 자동 병합할 수 없습니다.')
    if 'client' in names:
        op.rename_table('client', 'users')
    columns = {c['name'] for c in sa.inspect(db).get_columns('users')}
    for column in [
        sa.Column('last_login_at', sa.DateTime(), nullable=True, comment='마지막 로그인 시각(UTC)'),
        sa.Column('user_status', sa.SmallInteger().with_variant(TINYINT(), 'mysql'), nullable=False, server_default='1', comment=COMMENTS['users']['user_status']),
        sa.Column('auth', sa.SmallInteger().with_variant(TINYINT(), 'mysql'), nullable=False, server_default='0', comment=COMMENTS['users']['auth']),
    ]:
        if column.name not in columns:
            op.add_column('users', column)
    checks = {c['name'] for c in sa.inspect(db).get_check_constraints('users')}
    missing = [(name, expression) for name, expression in [
        ('ck_users_status', 'user_status IN (0,1,2,3)'), ('ck_users_auth', 'auth IN (0,1,9)')
    ] if name not in checks]
    if missing:
        with op.batch_alter_table('users') as batch:
            for name, expression in missing:
                batch.create_check_constraint(name, expression)
    stamp = db.execute(sa.select(sa.func.current_timestamp())).scalar_one()
    for table in sorted(sa.inspect(db).get_table_names()):
        if table not in COMMENTS:
            continue
        columns = {c['name']: c for c in sa.inspect(db).get_columns(table)}
        for field in ['create_at', 'update_at']:
            if field not in columns:
                op.add_column(table, sa.Column(field, sa.DateTime(), nullable=True))
            target = sa.table(table, sa.column(field, sa.DateTime()))
            db.execute(target.update().where(target.c[field].is_(None)).values({field: stamp}))
        # SQLite needs a table rebuild to install nonconstant defaults on existing rows.
        with op.batch_alter_table(table) as batch:
            batch.alter_column('create_at', existing_type=sa.DateTime(), nullable=False,
                server_default=sa.text('CURRENT_TIMESTAMP'), comment='생성 시각(UTC)')
            batch.alter_column('update_at', existing_type=sa.DateTime(), nullable=False,
                server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP'),
                comment='마지막 수정 시각(UTC)')
        if db.dialect.name == 'mysql':
            for column in sa.inspect(db).get_columns(table):
                comment = COMMENTS[table].get(column['name'])
                if comment is not None:
                    op.alter_column(table, column['name'], existing_type=column['type'],
                        existing_nullable=column['nullable'],
                        existing_server_default=sa.text(column['default']) if column.get('default') is not None else None,
                        autoincrement=column.get('autoincrement', False), comment=comment)


def downgrade():
    """계정 정책과 감사 기록을 보존하기 위해 역변환을 차단한다."""
    raise RuntimeError('감사 시각과 계정 상태를 보존하기 위해 자동 downgrade는 지원하지 않습니다.')
