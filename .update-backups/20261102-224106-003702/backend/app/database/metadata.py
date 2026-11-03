"""Alembic이 전체 모델을 발견하도록 한 곳에서 등록한다."""
from .base import Base
from ..modules.users.models import User, LoginSession
from ..modules.characters.models import Character, DeletedCharacter

# posts는 아직 테이블이 없다. 모델 구현 시 여기서 import한다.
from ..modules.items.models import Item, FarmingItem, DropItem
from ..modules.maps.models import Map, MapFarmingItem, MapMonster
from ..modules.monsters.models import Monster, MonsterDropItem
from ..modules.magic.models import Grimoire
from ..modules.recipes.models import Recipe
from ..modules.inventory.models import Inventory, InventoryEntry
from ..modules.exploration.models import Exploration

target_metadata = Base.metadata
