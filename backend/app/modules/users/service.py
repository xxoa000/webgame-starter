"""기능별 업무 규칙과 트랜잭션을 처리한다."""
import secrets
from datetime import timedelta
from fastapi import HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from ...core.config import settings
from ...core.dependencies import DB
from ...core.security import hasher, DUMMY_HASH, now, digest
from .models import User, LoginSession
from .schemas import Credentials
from .repository import find_by_username
from .models import User
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
    """비밀번호와 계정 상태를 검증하고 로그인 세션을 생성한다."""
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
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=digest(token), user_id=user.id,
        expires_at=now()+timedelta(hours=settings.session_hours)))
    db.commit()
    response.set_cookie("game_session", token, httponly=True, secure=settings.cookie_secure,
        samesite="lax", max_age=settings.session_hours*3600, path="/")
    return {"username": user.username}


def logout(request: Request, response: Response, db: DB):
    """로그인 세션과 인증 쿠키를 제거한다."""
    session = db.get(LoginSession, digest(request.cookies.get("game_session", "")))
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie("game_session", path="/")
    return {"message": "로그아웃했어."}
