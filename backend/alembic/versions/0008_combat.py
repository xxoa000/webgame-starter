"""몬스터 능력치·전투 상태와 맵별 몬스터·전리품을 추가한다."""
from alembic import op
import sqlalchemy as sa
revision = '0008_combat'
down_revision = '0007_apocalypse_world'
branch_labels = None
depends_on = None

ENEMIES = [
 ('폐허 주택가', '배회 감염체', 16, 2, 5, 0, 20, '오염된 조직 표본', 200),
 ('폐쇄된 지하철역', '암전 포식자', 22, 3, 7, 1, 25, '포식자의 감각 기관', 250),
 ('버려진 종합병원', '격리 병동 변이체', 24, 3, 8, 1, 25, '변이체 혈액 표본', 300),
 ('붕괴한 물류창고', '적재장 군집충', 20, 2, 6, 2, 20, '군집충 외피', 500),
 ('정지된 공업지대', '폭주 경비 드론', 30, 4, 8, 3, 30, '손상된 제어 코어', 800),
 ('오염 격리 검문소', '방호복 망령', 28, 4, 9, 2, 30, '부식된 식별 태그', 100),
 ('침수 지하상가', '침수 잠복체', 26, 3, 8, 1, 25, '잠복체 방수 막', 400),
 ('균열 관측소 잔해', '위상 침식자', 40, 5, 11, 3, 40, '불안정한 위상 핵', 900),
]


def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    db = op.get_bind()
    for table, definitions in {
        'monster': [('hp', sa.Integer(), '20'), ('attack_min', sa.Integer(), '2'),
                    ('attack_max', sa.Integer(), '5'), ('defense', sa.Integer(), '0')],
        'exploration': [('combat', sa.JSON(), None)],
    }.items():
        columns = {c['name'] for c in sa.inspect(db).get_columns(table)}
        for name, kind, default in definitions:
            if name not in columns:
                op.add_column(table, sa.Column(name, kind, nullable=name == 'combat', server_default=default))
    meta = sa.MetaData()
    meta.reflect(bind=db)
    t = meta.tables
    for map_name, name, hp, low, high, defense, weight, loot, grams in ENEMIES:
        map_id = db.execute(sa.select(t['map'].c.id).where(t['map'].c.name == map_name)).scalar_one_or_none()
        if map_id is None:
            continue
        monster_id = db.execute(sa.select(t['monster'].c.id).where(t['monster'].c.name == name)).scalar_one_or_none()
        if monster_id is None:
            result = db.execute(t['monster'].insert().values(name=name, description=f'{map_name}에서 관측된 위협 개체.', hp=hp,
                attack_min=low, attack_max=high, defense=defense))
            monster_id = result.inserted_primary_key[0]
        link = t['map_monster']
        if db.execute(sa.select(link).where(link.c.map_id == map_id, link.c.monster_id == monster_id)).first() is None:
            db.execute(link.insert().values(map_id=map_id, monster_id=monster_id, weight=weight))
        item_id = db.execute(sa.select(t['item'].c.id).where(t['item'].c.name == loot)).scalar_one_or_none()
        if item_id is None:
            result = db.execute(t['item'].insert().values(name=loot, description=f'{name}에게서 회수한 연구용 물자.', weight_grams=grams, kind='drop'))
            item_id = result.inserted_primary_key[0]
        if db.execute(sa.select(t['drop_item']).where(t['drop_item'].c.item_id == item_id)).first() is None:
            db.execute(t['drop_item'].insert().values(item_id=item_id))
        drops = t['monster_drop_item']
        if db.execute(sa.select(drops).where(drops.c.monster_id == monster_id, drops.c.drop_item_id == item_id)).first() is None:
            db.execute(drops.insert().values(monster_id=monster_id, drop_item_id=item_id, weight=100))


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError('진행 중인 전투와 소지 전리품 보존을 위해 자동 downgrade는 지원하지 않는다.')
