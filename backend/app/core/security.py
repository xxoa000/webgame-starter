"""세션 인증과 비밀번호·토큰 처리를 담당한다."""
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from .dependencies import DB
from ..modules.users.models import LoginSession, User
from ..modules.users.policy import ensure_active

hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("dummy-password-for-timing")

def now():
    """UTC 기준 현재 시각을 반환한다."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def digest(value):
    """세션 토큰의 단방향 해시를 생성한다."""
    return hashlib.sha256(value.encode()).hexdigest()

def current_user(request: Request, db: DB):
    """유효한 세션과 계정 상태를 검사해 사용자를 반환한다."""
    token = request.cookies.get("game_session", "")
    session = db.get(LoginSession, digest(token)) if token else None
    if not session or session.expires_at <= now():
        raise HTTPException(401, "로그인이 필요해.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "로그인이 필요해.")
    ensure_active(user)
    return user

Auth = Annotated[User, Depends(current_user)]
