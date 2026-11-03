"""성격·스크립트 초기 구조와 시드, 인적사항 수정 기회 및 삭제 보관을 추가한다."""
from alembic import op
import sqlalchemy as sa

revision = '0011_personality_scripts'
down_revision = '0010_posts'
branch_labels = None
depends_on = None

def upgrade():
    """기존 캐릭터를 보존하며 새 테이블과 고유 코드 기반 초기 데이터를 배치한다."""
    db = op.get_bind()
    for table, fields in {'character': [('name_changes', sa.Integer(), False, '0', '생성 후 이름 변경 횟수'), ('age_changes', sa.Integer(), False, '0', '생성 후 나이 변경 횟수')], 'deleted_character':[('personality_snapshot', sa.JSON(), True, None, '삭제 시 성격 선택 보관')]}.items():
        existing = {column['name'] for column in sa.inspect(db).get_columns(table)}
        for name, kind, nullable, default, comment in fields:
            if name not in existing:
                op.add_column(table, sa.Column(name, kind, nullable=nullable, server_default=default, comment=comment))
    if 'ck_character_profile_changes' not in {c['name'] for c in sa.inspect(db).get_check_constraints('character')}:
        with op.batch_alter_table('character') as batch:
            batch.create_check_constraint('ck_character_profile_changes', 'name_changes BETWEEN 0 AND 1 AND age_changes BETWEEN 0 AND 1')
    if 'personality_keyword' not in sa.inspect(db).get_table_names():
        op.create_table('personality_keyword',
            sa.Column('id', sa.Integer(), nullable=False, comment='성격 키워드 ID', primary_key=True),
            sa.Column('category', sa.String(12), nullable=False, comment='분류: OUTER겉 INNER속 ALIGNMENT성향'),
            sa.Column('code', sa.String(40), nullable=False, comment='성격 고유 코드'),
            sa.Column('name', sa.String(30), nullable=False, comment='성격 표시 이름'),
            sa.Column('description', sa.String(200), nullable=False, comment='성격 설명', server_default=''),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('code', name=None),
            sa.CheckConstraint("category IN ('OUTER','INNER','ALIGNMENT')", name='ck_keyword_category'),
            sa.UniqueConstraint('id', 'category', name='uq_keyword_id_category'),
        )

    if 'script_pack' not in sa.inspect(db).get_table_names():
        op.create_table('script_pack',
            sa.Column('id', sa.Integer(), nullable=False, comment='스크립트 묶음 ID', primary_key=True),
            sa.Column('code', sa.String(80), nullable=False, comment='묶음 고유 코드'),
            sa.Column('title', sa.String(100), nullable=False, comment='묶음 제목'),
            sa.Column('author_id', sa.Integer(), nullable=True, comment='작성자 ID, 시스템 시드는 NULL'),
            sa.Column('kind', sa.String(12), nullable=False, comment='종류: COMMON공통 PERSONAL개인 MARKET판매예정'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.UniqueConstraint('code', name=None),
            sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=None),
            sa.CheckConstraint("kind IN ('COMMON','PERSONAL','MARKET')", name='ck_pack_kind'),
        )

    if 'character_personality' not in sa.inspect(db).get_table_names():
        op.create_table('character_personality',
            sa.Column('id', sa.Integer(), nullable=False, comment='성격 선택 ID', primary_key=True),
            sa.Column('character_id', sa.Integer(), nullable=False, comment='캐릭터 ID'),
            sa.Column('category', sa.String(12), nullable=False, comment='선택 분류'),
            sa.Column('keyword_id', sa.Integer(), nullable=False, comment='선택한 성격 키워드 ID'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['character_id'], ['character.id'], name=None, ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['keyword_id', 'category'], ['personality_keyword.id', 'personality_keyword.category'], name='fk_character_keyword_category'),
            sa.UniqueConstraint('character_id', 'category', name='uq_character_category'),
        )

    if 'script_pack_version' not in sa.inspect(db).get_table_names():
        op.create_table('script_pack_version',
            sa.Column('id', sa.Integer(), nullable=False, comment='묶음 버전 ID', primary_key=True),
            sa.Column('pack_id', sa.Integer(), nullable=False, comment='원본 묶음 ID'),
            sa.Column('version', sa.Integer(), nullable=False, comment='버전 번호'),
            sa.Column('status', sa.String(12), nullable=False, comment='초안·심사·승인·비활성 상태', server_default='DRAFT'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['pack_id'], ['script_pack.id'], name=None),
            sa.CheckConstraint('version > 0', name='ck_pack_version_positive'),
            sa.CheckConstraint("status IN ('DRAFT','PENDING','APPROVED','DISABLED')", name='ck_pack_version_status'),
            sa.UniqueConstraint('pack_id', 'version', name='uq_pack_version'),
        )

    if 'character_script_pack' not in sa.inspect(db).get_table_names():
        op.create_table('character_script_pack',
            sa.Column('id', sa.Integer(), nullable=False, comment='캐릭터 적용 묶음 ID', primary_key=True),
            sa.Column('character_id', sa.Integer(), nullable=False, comment='사용할 캐릭터 ID'),
            sa.Column('version_id', sa.Integer(), nullable=False, comment='적용한 고정 버전 ID'),
            sa.Column('mode', sa.String(8), nullable=False, comment='전용 우선 PREFER 또는 공통 혼합 MIX', server_default='PREFER'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['version_id'], ['script_pack_version.id'], name=None),
            sa.ForeignKeyConstraint(['character_id'], ['character.id'], name=None, ondelete='CASCADE'),
            sa.CheckConstraint("mode IN ('PREFER','MIX')", name='ck_character_script_mode'),
            sa.UniqueConstraint('character_id', 'version_id', name='uq_character_script_version'),
        )

    if 'game_script' not in sa.inspect(db).get_table_names():
        op.create_table('game_script',
            sa.Column('id', sa.Integer(), nullable=False, comment='스크립트 ID', primary_key=True),
            sa.Column('code', sa.String(100), nullable=False, comment='스크립트 고유 코드'),
            sa.Column('version_id', sa.Integer(), nullable=False, comment='소속 묶음 버전 ID'),
            sa.Column('situation_code', sa.String(40), nullable=False, comment='상황 코드'),
            sa.Column('action_code', sa.String(40), nullable=True, comment='행동 코드, NULL이면 공통'),
            sa.Column('layer', sa.String(12), nullable=False, comment='발화·속마음·행동 서술 층'),
            sa.Column('visibility', sa.String(8), nullable=False, comment='PUBLIC공개 OWNER소유자전용'),
            sa.Column('content', sa.Text(), nullable=False, comment='허용된 변수만 포함한 대사 본문'),
            sa.Column('priority', sa.Integer(), nullable=False, comment='조건 일치 후보 중 우선순위', server_default='0'),
            sa.Column('weight', sa.Integer(), nullable=False, comment='동일 우선순위 내 추첨 가중치', server_default='100'),
            sa.Column('is_active', sa.Integer(), nullable=False, comment='사용 여부: 0비활성 1활성', server_default='1'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['version_id'], ['script_pack_version.id'], name=None),
            sa.UniqueConstraint('code', name=None),
            sa.CheckConstraint("layer IN ('SPEECH','THOUGHT','NARRATION')", name='ck_script_layer'),
            sa.CheckConstraint("(layer='SPEECH' AND visibility='PUBLIC') OR (layer IN ('THOUGHT','NARRATION') AND visibility='OWNER')", name='ck_script_visibility'),
            sa.CheckConstraint('weight > 0 AND is_active IN (0,1)', name='ck_script_weight_active'),
        )
    if 'ix_script_candidate' not in {index['name'] for index in sa.inspect(db).get_indexes('game_script')}:
        op.create_index('ix_script_candidate', 'game_script', ['situation_code', 'is_active', 'layer', 'version_id'], unique=False)

    if 'script_submission' not in sa.inspect(db).get_table_names():
        op.create_table('script_submission',
            sa.Column('id', sa.Integer(), nullable=False, comment='공통 등록 신청 ID', primary_key=True),
            sa.Column('version_id', sa.Integer(), nullable=False, comment='신청한 묶음 버전 ID'),
            sa.Column('applicant_id', sa.Integer(), nullable=False, comment='신청 사용자 ID'),
            sa.Column('reviewer_id', sa.Integer(), nullable=True, comment='심사 운영자 ID'),
            sa.Column('status', sa.String(12), nullable=False, comment='심사 상태', server_default='PENDING'),
            sa.Column('reward_amount', sa.Integer(), nullable=False, comment='예정된 무료 재화 보상', server_default='0'),
            sa.Column('reward_paid', sa.Integer(), nullable=False, comment='보상 처리 여부, 지급 기능은 미구현', server_default='0'),
            sa.Column('review_note', sa.String(500), nullable=False, comment='심사 의견', server_default=''),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['reviewer_id'], ['users.id'], name=None),
            sa.ForeignKeyConstraint(['applicant_id'], ['users.id'], name=None),
            sa.ForeignKeyConstraint(['version_id'], ['script_pack_version.id'], name=None),
            sa.CheckConstraint('reward_amount >= 0 AND reward_paid IN (0,1)', name='ck_submission_reward'),
            sa.CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name='ck_submission_status'),
            sa.UniqueConstraint('version_id', 'applicant_id', name='uq_script_submission'),
        )

    if 'user_script_pack' not in sa.inspect(db).get_table_names():
        op.create_table('user_script_pack',
            sa.Column('id', sa.Integer(), nullable=False, comment='묶음 사용권 ID', primary_key=True),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='사용권 보유 사용자 ID'),
            sa.Column('version_id', sa.Integer(), nullable=False, comment='사용 가능한 고정 버전 ID'),
            sa.Column('source', sa.String(20), nullable=False, comment='획득 경로: 작성·지급·향후 구매 등'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=None),
            sa.ForeignKeyConstraint(['version_id'], ['script_pack_version.id'], name=None),
            sa.UniqueConstraint('user_id', 'version_id', name='uq_user_script_version'),
        )

    if 'game_script_condition' not in sa.inspect(db).get_table_names():
        op.create_table('game_script_condition',
            sa.Column('id', sa.Integer(), nullable=False, comment='대사 적용 조건 ID', primary_key=True),
            sa.Column('script_id', sa.Integer(), nullable=False, comment='스크립트 ID'),
            sa.Column('condition_group', sa.Integer(), nullable=False, comment='그룹 내부 AND, 그룹 사이 OR', server_default='1'),
            sa.Column('keyword_id', sa.Integer(), nullable=True, comment='필수 성격 키워드 ID'),
            sa.Column('map_id', sa.Integer(), nullable=True, comment='대상 맵 ID'),
            sa.Column('hp_min_percent', sa.Integer(), nullable=True, comment='최소 HP 비율'),
            sa.Column('hp_max_percent', sa.Integer(), nullable=True, comment='최대 HP 비율'),
            sa.Column('create_at', sa.DateTime(), nullable=False, comment='생성 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('update_at', sa.DateTime(), nullable=False, comment='마지막 수정 시각(UTC)', server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP') if db.dialect.name == 'mysql' else sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['keyword_id'], ['personality_keyword.id'], name=None),
            sa.ForeignKeyConstraint(['script_id'], ['game_script.id'], name=None, ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['map_id'], ['map.id'], name=None),
            sa.CheckConstraint('condition_group > 0', name='ck_script_condition_group'),
            sa.CheckConstraint('keyword_id IS NOT NULL OR map_id IS NOT NULL OR hp_min_percent IS NOT NULL OR hp_max_percent IS NOT NULL', name='ck_script_condition_nonempty'),
            sa.CheckConstraint('(hp_min_percent IS NULL OR hp_min_percent BETWEEN 0 AND 100) AND (hp_max_percent IS NULL OR hp_max_percent BETWEEN 0 AND 100) AND (hp_min_percent IS NULL OR hp_max_percent IS NULL OR hp_min_percent <= hp_max_percent)', name='ck_script_hp_range'),
        )
    if 'ix_game_script_condition_script_id' not in {index['name'] for index in sa.inspect(db).get_indexes('game_script_condition')}:
        op.create_index('ix_game_script_condition_script_id', 'game_script_condition', ['script_id'], unique=False)

    seed_initial(db)

def downgrade():
    """확정된 성격과 스크립트 원문을 보존한다."""
    raise RuntimeError('성격과 스크립트 보존을 위해 자동 downgrade는 지원하지 않습니다.')

KEYWORDS = [
 (1, 'OUTER', 'OUTER_SHY', '소심함', '말을 조심스럽게 고르고 타인의 반응을 살핀다.'),
 (2, 'OUTER', 'OUTER_CHEERFUL', '쾌활함', '밝고 적극적인 태도로 말한다.'),
 (3, 'OUTER', 'OUTER_CYNICAL', '냉소적', '비꼬는 말투로 거리를 둔다.'),
 (4, 'OUTER', 'OUTER_SENSITIVE', '예민함', '작은 변화에도 날카롭게 반응한다.'),
 (11, 'INNER', 'INNER_FEARFUL', '겁많음', '위험을 두려워하고 안전을 바란다.'),
 (12, 'INNER', 'INNER_CARING', '다정함', '주변 사람의 안위를 신경 쓴다.'),
 (13, 'INNER', 'INNER_BRAVE', '용감함', '두려움보다 행동을 우선한다.'),
 (14, 'INNER', 'INNER_SELFISH', '이기적임', '자신의 생존과 이익을 우선한다.'),
 (21, 'ALIGNMENT', 'ALIGNMENT_GOOD', '선', '가능하면 타인에게 도움이 되는 길을 택한다.'),
 (22, 'ALIGNMENT', 'ALIGNMENT_NEUTRAL', '중립', '상황과 손익을 살펴 판단한다.'),
 (23, 'ALIGNMENT', 'ALIGNMENT_EVIL', '악', '타인보다 자신의 목적을 앞세운다.'),
]
EVENTS = {
 'empty': '회수할 물자를 찾지 못했다.',
 'found': '{item_name}을 발견했다.',
 'rest': '잠시 안전한 곳에서 쉬었다.',
 'encounter': '{monster_name}과 마주쳤다.',
 'victory': '위협 개체를 쓰러뜨렸다.',
 'flee': '위협으로부터 벗어났다.',
 'damage': '공격을 받아 다쳤다.',
 'death': '피계약자의 생체 신호가 끊겼다.',
}
# Two alternatives per keyword/layer: specific event prose can be edited independently in DB.
VOICES = {
 1: ('SPEECH', '저기… {summary}', '으음, 확인했어. {summary}'),
 2: ('SPEECH', '좋아, 보고할게! {summary}', '확인 완료! {summary}'),
 3: ('SPEECH', '참 성가시네. {summary}', '상황 한번 훌륭하군. {summary}'),
 4: ('SPEECH', '잠깐, 집중해. {summary}', '작은 소리도 놓치지 마. {summary}'),
 11: ('THOUGHT', '손끝이 떨린다. 더 위험해지지 않았으면.', '침착하자. 무사히 돌아가고 싶다.'),
 12: ('THOUGHT', '다른 사람들도 무사했으면 좋겠다.', '혼자만 괜찮다고 안심할 수는 없다.'),
 13: ('THOUGHT', '아직 버틸 수 있다. 다음 일에도 대비하자.', '주저앉을 때가 아니다. 정신을 붙잡자.'),
 14: ('THOUGHT', '우선 내 몫과 안전부터 지켜야 한다.', '남을 챙기기 전에 살아남는 게 먼저다.'),
 21: ('NARRATION', '주변에 도움을 필요로 하는 사람이 없는지 살핀다.', '다른 이에게 피해를 주지 않도록 주의를 기울인다.'),
 22: ('NARRATION', '주변 상황과 남은 자원을 차분히 가늠한다.', '위험과 이득을 비교하며 다음 지시를 기다린다.'),
 23: ('NARRATION', '자신에게 유리한 위치를 먼저 확인한다.', '다른 이의 사정보다 자신의 목적을 앞세운다.'),
}


def seed_initial(db):
    """기존 편집 데이터를 덮어쓰지 않고 고유 코드 기준으로 시드를 추가한다."""
    meta = sa.MetaData()
    meta.reflect(bind=db)
    t = meta.tables
    ids = {}
    for proposed_id, category, code, name, description in KEYWORDS:
        existing = db.execute(sa.select(t['personality_keyword'].c.id).where(t['personality_keyword'].c.code == code)).scalar_one_or_none()
        if existing is None:
            values = dict(category=category, code=code, name=name, description=description)
            # Stable initial IDs help manual inspection, but never overwrite a custom row.
            if not db.execute(sa.select(t['personality_keyword'].c.id).where(t['personality_keyword'].c.id == proposed_id)).first():
                values['id'] = proposed_id
            result = db.execute(t['personality_keyword'].insert().values(**values))
            existing = result.inserted_primary_key[0]
        ids[proposed_id] = existing
    pack_id = db.execute(sa.select(t['script_pack'].c.id).where(t['script_pack'].c.code == 'INITIAL_COMMON')).scalar_one_or_none()
    if pack_id is None:
        pack_id = db.execute(t['script_pack'].insert().values(code='INITIAL_COMMON', title='초기 공통 대사', author_id=None, kind='COMMON')).inserted_primary_key[0]
    version_id = db.execute(sa.select(t['script_pack_version'].c.id).where(t['script_pack_version'].c.pack_id == pack_id, t['script_pack_version'].c.version == 1)).scalar_one_or_none()
    if version_id is None:
        version_id = db.execute(t['script_pack_version'].insert().values(pack_id=pack_id, version=1, status='APPROVED')).inserted_primary_key[0]
    for event, summary in EVENTS.items():
        for layer in (('NARRATION',) if event == 'death' else ('SPEECH','THOUGHT','NARRATION')):
            add_script(db, t, f'{event}_COMMON_{layer}', version_id, event, layer, summary, 0, None)
        if event == 'death':
            continue  # Do not produce thoughts or living actions after death.
        for proposed_id, (layer, first, second) in VOICES.items():
            for index, text in enumerate((first,second),1):
                content = text.replace('{summary}', summary)
                add_script(db, t, f'{event}_K{proposed_id}_{index}', version_id, event, layer, content, 10, ids[proposed_id])

    for index, content in enumerate(('무섭지만… 누군가 다치기 전에 방법을 찾아야 해.', '저기… 다 같이 무사할 방법부터 생각해 보자.'),1):
        script_id = add_script(db, t, f'encounter_COMBO_{index}', version_id, 'encounter', 'SPEECH', content, 30, ids[1])
        if script_id is not None:
            for key in (11,21):
                db.execute(t['game_script_condition'].insert().values(script_id=script_id, condition_group=1, keyword_id=ids[key]))


def add_script(db, tables, code, version_id, event, layer, content, priority, keyword_id):
    """같은 코드의 원문을 보존하면서 대사와 조건을 초기 등록한다."""
    existing = db.execute(sa.select(tables['game_script'].c.id).where(tables['game_script'].c.code == code)).scalar_one_or_none()
    if existing is not None:
        return
    # Death only has public speech-like system report; owner layers remain private factual text.
    result = db.execute(tables['game_script'].insert().values(code=code, version_id=version_id,
        situation_code=event, action_code=None, layer=layer, visibility='PUBLIC' if layer == 'SPEECH' else 'OWNER',
        content=content, priority=priority, weight=100, is_active=1))
    if keyword_id is not None:
        db.execute(tables['game_script_condition'].insert().values(script_id=result.inserted_primary_key[0], condition_group=1, keyword_id=keyword_id))
    return result.inserted_primary_key[0]
