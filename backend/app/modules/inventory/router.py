"""HTTP 경로와 인증 의존성을 연결한다."""
from fastapi import APIRouter
from ...core.dependencies import DB
from ...core.security import Auth
from .schemas import InventoryResponse
from . import service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=InventoryResponse)
def get_inventory(user: Auth, db: DB):
    """소유 캐릭터의 인벤토리를 조회한다."""
    return service.get_inventory(db, user.id)
