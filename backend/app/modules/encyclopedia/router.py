"""HTTP 경로와 인증 의존성을 연결한다."""
from fastapi import APIRouter
from ...core.security import Auth
from ...core.dependencies import DB
from ..maps.service import list_maps
from .schemas import MapResponse

router=APIRouter(prefix='/encyclopedia',tags=['encyclopedia'])


@router.get('',response_model=list[MapResponse])
def get_encyclopedia(user:Auth,db:DB):
    """사용자 캐릭터의 맵별 발견 도감을 반환한다."""
    return list_maps(db,user.id)
