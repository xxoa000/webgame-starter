"""기능별 업무 규칙과 트랜잭션을 처리한다."""
from fastapi import HTTPException, Request, Response
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from ...core.config import settings
from ...core.dependencies import DB
from ...core.security import ACCESS_COOKIE, hasher, DUMMY_HASH, now, create_access_token, decode_access_token
from .models import User
from .schemas import Credentials
from .repository import find_by_username
from .policy import ACTIVE, INACTIVE


def signup(body: Credentials, db: DB):
    """중복 아이디를 검사하고 기본 권한으로 계정을 생성한다."""
    if find_by_username(db, body.username):
        raise HTTPException(409, "이미 사용 중인 아이디야.")
    db.add(User(username=body.username, password_hash=hasher.hash(body.password), auth=0, user_status=1))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용 중인 아이디야.")
    return {"message": "가입 완료. 로그인해."}


def login(body: Credentials, response: Response, db: DB):
    """비밀번호와 계정 상태를 검증하고 JWT 인증 토큰을 발급한다."""
    user = find_by_username(db, body.username)
    valid = hasher.verify(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "아이디 또는 비밀번호가 맞지 않아.")
    if user.user_status not in (INACTIVE, ACTIVE):
        raise HTTPException(403, '이용할 수 없는 계정이야.')
    # Serialize the state check with sanction changes; never reactivate a sanctioned account.
    db.refresh(user, with_for_update=True)
    if user.user_status not in (INACTIVE, ACTIVE):
        raise HTTPException(403, '이용할 수 없는 계정이야.')
    user.user_status = ACTIVE
    user.last_login_at = now()
    token = create_access_token(user)
    db.commit()
    response.delete_cookie("game_session", path="/")
    response.set_cookie(ACCESS_COOKIE, token, httponly=True, secure=settings.cookie_secure,
        samesite="lax", max_age=settings.jwt_access_hours*3600, path="/")
    return {"username": user.username}


def logout(request: Request, response: Response, db: DB):
    """JWT 버전을 원자적으로 증가시켜 계정의 기존 토큰을 모두 무효화한다."""
    token = request.cookies.get(ACCESS_COOKIE)
    if token:
        try:
            claims = decode_access_token(token)
        except HTTPException:
            claims = None
        if claims:
            db.execute(update(User).where(User.id == int(claims["sub"]),
                User.token_version == claims["ver"]).values(token_version=User.token_version + 1))
            db.commit()
    response.delete_cookie(ACCESS_COOKIE, path="/", httponly=True,
        secure=settings.cookie_secure, samesite="lax")
    response.delete_cookie("game_session", path="/")
    return {"message": "로그아웃했어."}
