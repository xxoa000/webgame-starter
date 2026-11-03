"""초기 성격 11개와 편집 가능한 공통 스크립트 예시를 정의한다."""
import sqlalchemy as sa

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
