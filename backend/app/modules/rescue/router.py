"""인증된 구조 요청·포기와 동일 맵 구조 지원 API를 연결한다."""
from fastapi import APIRouter, Path
from ...core.security import Auth
from ...core.dependencies import DB
from . import service
router=APIRouter(prefix='/rescue',tags=['rescue'])


@router.post('/request')
def request(user:Auth,db:DB):
    """소유 피계약자의 구조를 요청한다."""
    return service.owner_action(db,user.id,'request')


@router.post('/abandon')
def abandon(user:Auth,db:DB):
    """구조를 포기하고 사망을 확정한다."""
    return service.owner_action(db,user.id,'abandon')


@router.get('/nearby')
def nearby(user:Auth,db:DB):
    """동일 맵에 있는 구조 대기자를 조회한다."""
    return service.nearby(db,user.id)


@router.post('/{request_id}/help')
def help_player(user:Auth,db:DB,request_id:int=Path(gt=0)):
    """대상 피계약자를 구조한다."""
    return service.help_player(db,user.id,request_id)
