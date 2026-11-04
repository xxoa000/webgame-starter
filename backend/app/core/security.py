"""JWT 서명·만료 검증과 DB 기반 계정 상태·권한 확인을 담당한다."""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any
import secrets
import jwt
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from .config import settings
from .dependencies import DB
from ..modules.users.models import User
from ..modules.users.policy import ensure_active

ACCESS_COOKIE = "game_access"
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "webgame-backend"
JWT_AUDIENCE = "webgame-client"
hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("dummy-password-for-timing")


def now() -> datetime:
    """DB에 저장하는 시간대 없는 UTC 시각을 반환한다."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def create_access_token(user: User) -> str:
    """사용자 ID와 무효화 버전을 담은 만료 가능한 JWT를 발급한다."""
    issued = datetime.now(timezone.utc)
    return jwt.encode({
        "sub": str(user.id), "ver": user.token_version,
        "iat": issued, "nbf": issued,
        "exp": issued + timedelta(hours=settings.jwt_access_hours),
        "iss": JWT_ISSUER, "aud": JWT_AUDIENCE,
        "token_type": "access", "jti": secrets.token_urlsafe(16),
    }, settings.signing_key(), algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """고정 알고리즘으로 서명·시간·발급자·대상·필수 클레임을 검증한다."""
    try:
        claims = jwt.decode(token, settings.signing_key(), algorithms=[JWT_ALGORITHM],
            issuer=JWT_ISSUER, audience=JWT_AUDIENCE,
            options={"require": ["sub", "ver", "iat", "nbf", "exp", "iss", "aud", "token_type", "jti"]})
        subject = claims["sub"]
        if (not isinstance(subject, str) or not subject.isascii() or not subject.isdigit()
                or len(subject) > 19 or int(subject) <= 0
                or type(claims["ver"]) is not int or claims["ver"] < 0
                or claims["token_type"] != "access"
                or not isinstance(claims["jti"], str) or not claims["jti"]):
            raise jwt.InvalidTokenError()
        return claims
    except jwt.InvalidTokenError:
        raise HTTPException(401, "로그인이 필요해.") from None


def current_user(request: Request, db: DB) -> User:
    """JWT와 무효화 버전을 확인하고 최신 DB 권한의 사용자를 반환한다."""
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(401, "로그인이 필요해.")
    claims = decode_access_token(token)
    user = db.get(User, int(claims["sub"]))
    if not user or user.token_version != claims["ver"]:
        raise HTTPException(401, "로그인이 필요해.")
    ensure_active(user)
    return user


Auth = Annotated[User, Depends(current_user)]
