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


@router.get("/presence")
def presence_counts(user: Auth, db: DB):
    """인증 사용자에게 맵별 온라인 탐사 인원을 반환한다."""
    from .presence import counts
    return counts(db)


@router.post("/presence")
def presence_heartbeat(user: Auth, db: DB):
    """탐색 화면 접속 신호를 갱신하고 맵별 인원을 반환한다."""
    from .presence import heartbeat
    return heartbeat(db, user.id)
