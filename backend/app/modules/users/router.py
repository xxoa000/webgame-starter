"""HTTP 경로와 인증 의존성을 연결한다."""
from typing import Annotated
from fastapi import APIRouter, Request, Response
from pydantic import Field
from ...core.dependencies import DB
from .schemas import Credentials
from . import repository, service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/check-username")
def check_username(username: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")], db: DB):
    """로그인 아이디의 중복 여부를 검사한다."""
    return {"available": repository.find_by_username(db, username.lower()) is None}


@router.post("/signup", status_code=201)
def signup(body: Credentials, db: DB):
    """중복 아이디를 검사하고 기본 권한으로 계정을 생성한다."""
    return service.signup(body, db)


@router.post("/login")
def login(body: Credentials, response: Response, db: DB):
    """비밀번호와 계정 상태를 검증하고 JWT 인증 토큰을 발급한다."""
    return service.login(body, response, db)


@router.post("/logout")
def logout(request: Request, response: Response, db: DB):
    """기존 JWT를 무효화하고 인증 쿠키를 제거한다."""
    return service.logout(request, response, db)
