"""기존 숲 시드와 관련 기록을 제거하고 아포칼립스 맵·파밍 물자를 배치한다."""
from alembic import op
import sqlalchemy as sa

revision = "0007_apocalypse_world"
down_revision = "0006_character_appearance"
branch_labels = None
depends_on = None

ITEMS = [('밀봉 생수', '봉인이 남아 있는 식수.', 1000),
 ('통조림 식량', '포장이 보존된 비상 식량.', 450),
 ('보온 담요', '체온 유지를 위한 은박 담요.', 200),
 ('구리 전선', '절연 피복이 남은 전선.', 350),
 ('휴대용 전지', '잔량 확인이 필요한 전지.', 180),
 ('교통 단말 부품', '폐쇄된 개찰구의 전자 부품.', 300),
 ('멸균 붕대', '밀봉된 응급 처치 재료.', 80),
 ('소독제', '외부 오염을 닦는 소독액.', 500),
 ('응급 처치 키트', '붕대와 의료 소모품 묶음.', 1200),
 ('결속 케이블', '물자 고정용 케이블 묶음.', 150),
 ('공구 세트', '소형 수리 공구가 들어 있는 가방.', 2500),
 ('휴대용 정수 필터', '교체형 여과 장치.', 400),
 ('금속 스크랩', '재가공 가능한 금속 조각.', 1800),
 ('기계 윤활유', '기계 유지 보수용 밀봉 용기.', 900),
 ('산업용 축전지', '무겁지만 용량이 큰 축전지.', 6000),
 ('방진 필터', '방독면용 교환 필터.', 250),
 ('보호 장갑', '두꺼운 산업용 보호 장갑.', 300),
 ('오염 측정기', '잔류 오염을 측정하는 장치.', 850),
 ('방수 천', '찢어지지 않은 방수 자재.', 700),
 ('밀봉 연료통', '누출 여부를 확인해야 하는 연료.', 3500),
 ('방수 보관함', '침수에도 내부가 보존된 상자.', 1300),
 ('관측 기록 매체', '균열 관측 로그가 남은 저장 매체.', 100),
 ('차폐 합금 파편', '이상 에너지 차폐용 합금 조각.', 2200),
 ('위상 잔류 결정', '균열 주변에서 고형화된 미확인 물질.', 600)]
MAPS = [('폐허 주택가', '무너진 주거 구역. 생존자들이 남긴 생활 물자를 수색한다.', 55, [(0, 25), (1, 15), (2, 5)]),
 ('폐쇄된 지하철역', '정전된 승강장과 통제실에 전자 부품이 남아 있다.', 60, [(3, 22), (4, 13), (5, 5)]),
 ('버려진 종합병원', '격리 병동과 처치실에서 밀봉 의료 물자를 찾는다.', 60, [(6, 23), (7, 13), (8, 4)]),
 ('붕괴한 물류창고', '무너진 선반 아래에 공구와 비상 물자가 묻혀 있다.', 50, [(9, 25), (10, 15), (11, 10)]),
 ('정지된 공업지대', '가동이 멈춘 생산 설비 주변에 산업 자재가 남아 있다.', 55, [(12, 25), (13, 15), (14, 5)]),
 ('오염 격리 검문소', '철수한 대응 인력이 남긴 보호 장비를 수색한다.', 65, [(15, 20), (16, 12), (17, 3)]),
 ('침수 지하상가', '고인 물과 잔해 사이에 방수 물자가 떠밀려 있다.', 60, [(18, 23), (19, 12), (20, 5)]),
 ('균열 관측소 잔해', '폐기된 관측 장비 주위에 불안정한 잔류 물질이 남아 있다.', 70, [(21, 18), (22, 9), (23, 3)])]

def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    db = op.get_bind()
    meta = sa.MetaData()
    meta.reflect(bind=db)
    t = meta.tables
    old_items = list(db.execute(sa.select(t['item'].c.id).where(t['item'].c.name.in_([
        '정체를 알 수 없는 버섯', '희미한 빛을 띄는 버섯', '붉은 잎 약초', '푸른 마나 열매'
    ]))).scalars())
    old_maps = list(db.execute(sa.select(t['map'].c.id).where(t['map'].c.name.in_(['깊은 숲1', '깊은 숲3']))).scalars())
    if old_items:
        e = t['exploration']
        db.execute(e.update().where(e.c.pending_item_id.in_(old_items)).values(pending_item_id=None, pending_quantity=0, version=e.c.version + 1))
        for name, column in [('inventory_entry','item_id'), ('encyclopedia','item_id'), ('map_farming_item','farming_item_id'), ('monster_drop_item','drop_item_id')]:
            if name in t:
                db.execute(t[name].delete().where(t[name].c[column].in_(old_items)))
        r = t['recipe']
        db.execute(r.delete().where(sa.or_(*[r.c[c].in_(old_items) for c in ['main_item_id','sub_item1_id','sub_item2_id','result_item_id']])))
        for name, column in [('farming_item','item_id'), ('drop_item','item_id'), ('item','id')]:
            db.execute(t[name].delete().where(t[name].c[column].in_(old_items)))
    if old_maps:
        db.execute(t['exploration'].delete().where(t['exploration'].c.map_id.in_(old_maps)))
        db.execute(t['encyclopedia'].update().where(t['encyclopedia'].c.first_map_id.in_(old_maps)).values(first_map_id=None))
        for name in ['map_farming_item','map_monster']:
            db.execute(t[name].delete().where(t[name].c.map_id.in_(old_maps)))
        db.execute(t['map'].delete().where(t['map'].c.id.in_(old_maps)))
    item_ids = []
    for name, description, grams in ITEMS:
        item_id = db.execute(sa.select(t['item'].c.id).where(t['item'].c.name == name)).scalar_one_or_none()
        if item_id is None:
            result = db.execute(t['item'].insert().values(name=name, description=description, weight_grams=grams, kind='farming'))
            item_id = result.inserted_primary_key[0]
        item_ids.append(item_id)
        if db.execute(sa.select(t['farming_item']).where(t['farming_item'].c.item_id == item_id)).first() is None:
            db.execute(t['farming_item'].insert().values(item_id=item_id))
    for name, description, empty, loot in MAPS:
        map_id = db.execute(sa.select(t['map'].c.id).where(t['map'].c.name == name)).scalar_one_or_none()
        if map_id is None:
            result = db.execute(t['map'].insert().values(name=name, description=description, empty_weight=empty))
            map_id = result.inserted_primary_key[0]
        for index, weight in loot:
            link = t['map_farming_item']
            condition = sa.and_(link.c.map_id == map_id, link.c.farming_item_id == item_ids[index])
            if db.execute(sa.select(link).where(condition)).first() is None:
                db.execute(link.insert().values(map_id=map_id, farming_item_id=item_ids[index], weight=weight))


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError('삭제된 이전 탐색·아이템 기록은 복구할 수 없다. 적용 전 DB 백업으로 복원해야 한다.')
