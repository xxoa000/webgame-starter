from fastapi import APIRouter
from ...core.dependencies import DB
from ...core.security import Auth
from .schemas import MapResponse
from . import service

router = APIRouter(prefix="/maps", tags=["maps"])


@router.get("", response_model=list[MapResponse])
def list_maps(user: Auth, db: DB):
    return service.list_maps(db)
