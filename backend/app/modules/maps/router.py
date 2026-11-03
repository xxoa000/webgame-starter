"""HTTP 경로와 인증 의존성을 연결한다."""
from fastapi import APIRouter
from ...core.dependencies import DB
from ...core.security import Auth
from .schemas import MapResponse
from . import service

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("", response_model=list[MapResponse])
def list_maps(user: Auth, db: DB):
    """공개 맵 목록과 발견 가능한 물자 확률을 조회한다."""
    return service.list_maps(db,user.id)
