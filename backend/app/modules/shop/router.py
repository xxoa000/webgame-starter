""" 인증된 사용자에게 상점 조회·구매·판매 API를 제공한다. """
from fastapi import APIRouter
from ...core.dependencies import DB
from ...core.security import Auth
from .schemas import TradeRequest
from . import service
router=APIRouter(prefix='/shop',tags=['shop'])


@router.get('')
def catalog(user:Auth,db:DB):
    """상점 상품 목록을 조회한다."""
    return service.catalog(db,user.id)


@router.post('/buy')
def buy(body:TradeRequest,user:Auth,db:DB):
    """서버 가격으로 상품을 구매한다."""
    return service.trade(db,user.id,body,True)


@router.post('/sell')
def sell(body:TradeRequest,user:Auth,db:DB):
    """보유 물품을 지정 수량만큼 판매한다."""
    return service.trade(db,user.id,body,False)


from .schemas import UpgradeRequest


@router.get('/upgrades')
def list_upgrades(user: Auth, db: DB):
    """영구 상품과 가격을 반환한다."""
    return service.upgrades(db, user.id)


@router.post('/upgrades/buy')
def purchase_upgrade(body: UpgradeRequest, user: Auth, db: DB):
    """구매 대금과 영구 확장 효과를 함께 적용한다."""
    return service.buy_upgrade(db, user.id, body)
