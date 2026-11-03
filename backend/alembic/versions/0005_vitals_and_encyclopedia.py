"""외모·키 제거, 남은 재추첨 횟수, HP/MP/스태미나와 개인 도감."""
from datetime import datetime, timezone
from alembic import op
import sqlalchemy as sa

revision='0005_vitals_encyclopedia'
down_revision='0004_exploration_inventory'
branch_labels=None
depends_on=None


def upgrade():
    """해당 리비전의 스키마와 데이터 변경을 적용한다."""
    connection=op.get_bind()
    columns={row['name'] for row in sa.inspect(connection).get_columns('character')}
    for name in ('hp_current','mp_current','stamina_current'):
        if name not in columns:
            op.add_column('character',sa.Column(name,sa.Integer(),nullable=True))
    if 'stamina_updated_at' not in columns:
        op.add_column('character',sa.Column('stamina_updated_at',sa.DateTime(),nullable=True))
    if not sa.inspect(connection).has_table('encyclopedia'):
        op.create_table('encyclopedia',
            sa.Column('id',sa.Integer(),primary_key=True),
            sa.Column('character_id',sa.Integer(),sa.ForeignKey('character.id',ondelete='CASCADE'),nullable=False),
            sa.Column('item_id',sa.Integer(),sa.ForeignKey('item.id'),nullable=False),
            sa.Column('first_map_id',sa.Integer(),sa.ForeignKey('map.id'),nullable=True),
            sa.Column('discovered_at',sa.DateTime(),nullable=False),
            sa.UniqueConstraint('character_id','item_id',name='uq_encyclopedia_character_item'))
    else:
        required={'id','character_id','item_id','first_map_id','discovered_at'}
        if not required <= {row['name'] for row in sa.inspect(connection).get_columns('encyclopedia')}:
            raise RuntimeError('encyclopedia 테이블 구조가 예상과 달라. 기존 데이터는 변경하지 않았어.')
    # All DDL is above this point. Conversion and version recording share the DML transaction.
    stamp=datetime.now(timezone.utc).replace(tzinfo=None)
    character=sa.Table('character',sa.MetaData(),autoload_with=connection)
    for row in connection.execute(sa.select(character)).mappings().all():
        stats={key:value for key,value in row['stats'].items() if key not in {'appearance','height_cm'}}
        ready=row['status']=='ready'
        connection.execute(character.update().where(character.c.id==row['id']).values(
            stats=stats,rerolls=10-row['rerolls'],
            hp_current=stats['stamina']*10 if ready else None,
            mp_current=stats['intelligence']*10 if ready else None,
            stamina_current=stats['agility'] if ready else None,stamina_updated_at=stamp if ready else None))
    archive=sa.Table('deleted_character',sa.MetaData(),autoload_with=connection)
    for row in connection.execute(sa.select(archive)).mappings().all():
        connection.execute(archive.update().where(archive.c.id==row['id']).values(
            stats={key:value for key,value in row['stats'].items() if key not in {'appearance','height_cm'}},
            rerolls=10-row['rerolls']))
    encyclopedia=sa.Table('encyclopedia',sa.MetaData(),autoload_with=connection)
    known=set(connection.execute(sa.select(encyclopedia.c.character_id,encyclopedia.c.item_id)).all())
    def discover(character_id,item_id,map_id=None):
        """최초 발견한 아이템을 캐릭터 도감에 기록한다."""
        key=(character_id,item_id)
        if key not in known:
            connection.execute(encyclopedia.insert().values(character_id=character_id,item_id=item_id,first_map_id=map_id,discovered_at=stamp))
            known.add(key)
    for row in connection.execute(sa.text('SELECT i.character_id,e.item_id FROM inventory i JOIN inventory_entry e ON e.inventory_id=i.id')).mappings():
        discover(row['character_id'],row['item_id'])
    items=sa.Table('item',sa.MetaData(),autoload_with=connection)
    item_names={row.id:row.name for row in connection.execute(sa.select(items.c.id,items.c.name))}
    exploration=sa.Table('exploration',sa.MetaData(),autoload_with=connection)
    for row in connection.execute(sa.select(exploration)).mappings().all():
        if row['pending_item_id']:
            discover(row['character_id'],row['pending_item_id'],row['map_id'])
        for event in row['history']:
            if event.get('kind')=='found':
                for item_id,name in item_names.items():
                    if event.get('message')==f"'{name}'을 발견했다.":
                        discover(row['character_id'],item_id,row['map_id'])


def downgrade():
    """해당 리비전의 역변환 지원 여부를 처리한다."""
    raise RuntimeError('도감과 자원 상태를 보존하기 위해 자동 downgrade는 지원하지 않아. 백업으로 복원해.')
