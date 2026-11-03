"""Register all tables; actual model definitions live in their feature modules."""
from .modules.auth.models import User, LoginSession
from .modules.characters.models import Character, DeletedCharacter

__all__ = ["User", "LoginSession", "Character", "DeletedCharacter"]
