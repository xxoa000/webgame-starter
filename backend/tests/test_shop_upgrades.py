"""영구 구매·스탯 분배의 잔액/버전 검증과 등급 경계·DB 보존을 확인한다."""
import pytest
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from test_flow import client
from test_exploration import world, start
from test_alembic import config_for
from app.modules.users.models import User
from app.modules.characters.models import Character
from app.modules.shop.models import ShopUpgrade
from app.modules.items.presentation import rarity_for
from app.database.metadata import target_metadata


@pytest.fixture
def shop(world):
    """테스트 상품과 충분한 무료 재화를 준비한다."""
    c, factory, character = world
    with factory.begin() as db:
        db.scalar(sa.select(User)).money = 10000
        db.add_all([ShopUpgrade(code='bag_expansion', name='가방 확장', description='확장', price=1000), ShopUpgrade(code='stat_point', name='스탯 포인트 +1', description='포인트', price=1000)])
    return c, factory, character


def test_capacity_stacks_and_does_not_occupy_slots(shop):
    """반복·복수 구매의 용량 증가와 잔액을 함께 확인한다."""
    c, _, _ = shop
    result = c.post('/shop/upgrades/buy', json={'code': 'bag_expansion', 'quantity': 2})
    assert result.status_code == 200, result.text
    data = result.json()
    assert (data['slot_capacity'], data['max_weight_grams'], data['money'], data['used_slots']) == (12, 50000, 8000, 0)
    again = c.post('/shop/upgrades/buy', json={'code': 'bag_expansion'}).json()
    assert (again['slot_capacity'], again['max_weight_grams'], again['money']) == (13, 60000, 7000)
    before = c.get('/inventory').json()
    assert c.post('/shop/upgrades/buy', json={'code': 'bag_expansion', 'quantity': 99}).status_code == 409
    assert c.get('/inventory').json() == before
    for body in ({'code': 'unknown'}, {'code': 'stat_point', 'price': 1}, {'code': 'bag_expansion', 'quantity': True}):
        assert c.post('/shop/upgrades/buy', json=body).status_code == 422


def test_stat_points_allocation_replay_and_overdraft(shop):
    """구매 포인트만 분배하며 동일 버전 재사용·음수·과다 분배를 거절한다."""
    c, _, _ = shop
    assert c.post('/shop/upgrades/buy', json={'code': 'stat_point', 'quantity': 2}).status_code == 200
    character = c.get('/me').json()['character']
    assert character['stat_points'] == 2
    body = {'version': character['stat_version'], 'strength': 1, 'luck': 1}
    allocated = c.post('/characters/stats/allocate', json=body)
    assert allocated.status_code == 200, allocated.text
    data = allocated.json()
    assert data['stat_points'] == 0
    assert data['stats']['strength'] == character['stats']['strength'] + 1
    assert data['stats']['luck'] == character['stats']['luck'] + 1
    assert data['vitals']['hp_current'] == character['vitals']['hp_current']
    assert c.post('/characters/stats/allocate', json=body).status_code == 409
    assert c.post('/characters/stats/allocate', json={'version': data['stat_version'], 'strength': 1}).status_code == 409
    assert c.post('/characters/stats/allocate', json={'version': data['stat_version'], 'luck': -1}).status_code == 422
    assert c.post('/characters/stats/allocate', json={'version': data['stat_version'], 'luck': True}).status_code == 422
    assert c.get('/me').json()['character']['stats'] == data['stats']


def test_allocation_requires_ending_exploration_and_living_character(shop):
    """탐색 중 분배와 빈사 구매를 차단한다."""
    c, factory, character = shop
    c.post('/shop/upgrades/buy', json={'code': 'stat_point'})
    data = c.get('/me').json()['character']
    start(c)
    assert c.post('/characters/stats/allocate', json={'version': data['stat_version'], 'stamina': 1}).status_code == 409
    with factory.begin() as db:
        db.get(Character, character['id']).downed = True
    assert c.post('/shop/upgrades/buy', json={'code': 'bag_expansion'}).status_code == 409


@pytest.mark.parametrize('chance,event,grade', [(None,False,'common'),(.60,False,'common'),(.30,False,'uncommon'),(.15,False,'rare'),(.07,False,'epic'),(.03,False,'legendary'),(.01,False,'legendary'),(.01,True,'mythic'),(.011,True,'legendary'),(.30001,False,'common')])
def test_rarity_boundaries(chance,event,grade):
    """중첩 경계는 낮은 확률부터 판정하고 mythic은 이벤트 물품만 허용한다."""
    assert rarity_for(chance,event) == grade


def test_migration_preserves_prices_and_matches_models(tmp_path):
    """운영자가 수정한 가격을 덮어쓰지 않으며 신규 값만 추가한다."""
    engine = sa.create_engine('sqlite:///' + str(tmp_path/'upgrades.db'))
    with engine.connect() as db:
        command.upgrade(config_for(db), '0016_jwt_auth')
        item_id = db.execute(sa.text('SELECT id FROM item ORDER BY id LIMIT 1')).scalar_one()
        db.execute(sa.text('UPDATE item SET buy_price=12345 WHERE id=:id'), {'id':item_id})
        db.commit()
        command.upgrade(config_for(db), 'head')
        assert db.execute(sa.text('SELECT buy_price FROM item WHERE id=:id'), {'id':item_id}).scalar_one() == 12345
        assert db.execute(sa.text('SELECT COUNT(*) FROM shop_upgrade')).scalar_one() == 2
        assert db.execute(sa.text("SELECT edible FROM item WHERE name='밀봉 생수'")).scalar_one()
        assert compare_metadata(MigrationContext.configure(db), target_metadata) == []
    engine.dispose()
