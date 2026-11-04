"""HTTP 경로와 인증 의존성을 연결한다."""
from fastapi import APIRouter
from ...core.dependencies import DB
from ...core.security import Auth
from .schemas import InventoryResponse, InventoryAction
from . import service

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("", response_model=InventoryResponse)
def get_inventory(user: Auth, db: DB):
    """소유 캐릭터의 인벤토리를 조회한다."""
    return service.get_inventory(db, user.id)


@router.post('/use',response_model=InventoryResponse)
def use_item(body:InventoryAction,user:Auth,db:DB):
    """턴 소모 없이 소유 회복 아이템을 사용한다."""
    return service.change_item(db,user.id,body,True)


@router.post('/discard',response_model=InventoryResponse)
def discard(body:InventoryAction,user:Auth,db:DB):
    """지정한 수량의 소지품을 버린다."""
    return service.change_item(db,user.id,body,False)
