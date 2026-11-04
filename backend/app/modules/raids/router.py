"""공개 균열 경보와 인증된 공유 보스 공격 경로를 제공한다."""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from ...core.dependencies import DB
from ...core.security import Auth
from . import service

router = APIRouter(prefix='/raids', tags=['raids'])


class RaidAttack(BaseModel):
    model_config = {'extra': 'forbid'}
    version: int = Field(gt=0, strict=True)


@router.get('/current')
def public_current(db: DB):
    """홈·지도에서 로그인 없이 현재 이벤트를 확인한다."""
    return service.current(db)


@router.get('/mine')
def my_current(user: Auth, db: DB):
    """현재 이벤트와 개인 수집·정산 현황을 확인한다."""
    return service.current(db, user.id)


@router.post('/{event_id}/attack')
def attack(event_id: int, body: RaidAttack, user: Auth, db: DB):
    """공유 HP를 변경하는 공격은 버전 검증 후 한 번만 처리한다."""
    return service.attack(db, user.id, event_id, body.version)
