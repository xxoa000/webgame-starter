"""가득 찬 배낭에서 물품을 버리고 대기 중인 발견을 회수하는 흐름을 검증한다."""
import pytest
from sqlalchemy import select
from test_flow import client
from test_exploration import world, start, act, force_draw
from test_combat import battlefield
from app.modules.items.models import Item
from app.modules.inventory.models import Inventory, InventoryEntry


@pytest.mark.parametrize('limit', ['slots', 'weight'])
def test_discard_then_take_pending_discovery(world, monkeypatch, limit):
    """용량 초과 회수 실패 후 버리기는 발견을 보존하고 최신 버전으로 재회수된다."""
    c, factory, _ = world
    with factory.begin() as db:
        inventory = db.scalar(select(Inventory))
        if limit == 'slots':
            for index in range(10):
                item = Item(name=f'교체 검증 {index}', description='', weight_grams=1, kind='crafted')
                db.add(item)
                db.flush()
                db.add(InventoryEntry(inventory_id=inventory.id, item_id=item.id, quantity=1))
        else:
            db.add(InventoryEntry(inventory_id=inventory.id, item_id=1, quantity=150))
    state = start(c)
    force_draw(monkeypatch, 70)
    found_response = act(c, state, 'search')
    assert found_response.status_code == 200, found_response.text
    found = found_response.json()
    assert act(c, found, 'take').status_code == 409
    before = c.get('/inventory').json()
    item = before['items'][0]
    discarded = c.post('/inventory/discard', json={'item_id': item['item_id'], 'quantity': 1})
    assert discarded.status_code == 200, discarded.text
    refreshed = c.get('/exploration/state').json()
    assert refreshed['pending_item'] == found['pending_item']
    assert refreshed['turn'] == found['turn']
    assert refreshed['version'] > found['version']
    taken = act(c, refreshed, 'take')
    assert taken.status_code == 200, taken.text
    assert taken.json()['pending_item'] is None
    assert taken.json()['turn'] == found['turn']
    after = c.get('/inventory').json()
    assert after['money'] == before['money']
    assert after['used_slots'] <= after['slot_capacity']
    assert after['current_weight_grams'] <= after['max_weight_grams']


def test_departing_combat_can_flee_then_end(battlefield):
    """화면 이탈에 쓰는 도망·종료는 각각 최신 버전을 사용하며 반격이 없다."""
    c, _, _, state, _ = battlefield
    fled = act(c, state, 'flee')
    assert fled.status_code == 200, fled.text
    safe = fled.json()
    assert safe['combat'] is None
    assert safe['vitals']['hp_current'] == state['vitals']['hp_current']
    ended = act(c, safe, 'end')
    assert ended.status_code == 200, ended.text
    assert ended.json()['status'] == 'ended'
