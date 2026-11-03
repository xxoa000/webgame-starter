"""HTTP 경로와 인증 의존성을 연결한다."""
from fastapi import APIRouter
from ...core.dependencies import DB
from ...core.security import Auth
from .schemas import StartExploration, ExplorationAction
from . import service

router = APIRouter(prefix="/exploration", tags=["exploration"])


@router.get("/state")
def get_state(user: Auth, db: DB):
    """현재 캐릭터의 탐색 상태를 조회한다."""
    return service.get_state(db, user.id)


@router.post("/start")
def start(body: StartExploration, user: Auth, db: DB):
    """맵을 확인하고 탐색을 시작하거나 기존 상태를 반환한다."""
    return service.start(db, user.id, body.map_id)


@router.post("/action")
def act(body: ExplorationAction, user: Auth, db: DB):
    """턴 버전과 선택지를 검사하고 탐색 행동을 실행한다."""
    return service.act(db, user.id, body)
