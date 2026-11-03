"""Alembic이 전체 모델을 발견하도록 한 곳에서 등록한다."""
from .base import Base
from ..modules.users.models import User, LoginSession
from ..modules.characters.models import Character, DeletedCharacter

from ..modules.posts.models import Post
from ..modules.items.models import Item, FarmingItem, DropItem
from ..modules.maps.models import Map, MapFarmingItem, MapMonster
from ..modules.monsters.models import Monster, MonsterDropItem
from ..modules.skill.models import Skill
from ..modules.recipes.models import Recipe
from ..modules.inventory.models import Inventory, InventoryEntry
from ..modules.exploration.models import Exploration

from ..modules.encyclopedia.models import Encyclopedia

target_metadata = Base.metadata

from ..modules.personality.models import PersonalityKeyword, CharacterPersonality
from ..modules.scripts.models import ScriptPack, ScriptPackVersion, GameScript, GameScriptCondition, ScriptSubmission, UserScriptPack, CharacterScriptPack
