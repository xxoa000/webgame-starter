import secrets
from datetime import timedelta
from fastapi import HTTPException, Request, Response
from sqlalchemy.exc import IntegrityError
from ...config import settings
from ...core.dependencies import DB
from ...core.security import hasher, DUMMY_HASH, now, digest
from .models import User, LoginSession
from .schemas import Credentials
from .repository import find_by_username


def signup(body: Credentials, db: DB):
    if find_by_username(db, body.username):
        raise HTTPException(409, "이미 사용 중인 아이디야.")
    db.add(User(username=body.username, password_hash=hasher.hash(body.password)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용 중인 아이디야.")
    return {"message": "가입 완료. 로그인해."}


def login(body: Credentials, response: Response, db: DB):
    user = find_by_username(db, body.username)
    valid = hasher.verify(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "아이디 또는 비밀번호가 맞지 않아.")
    token = secrets.token_urlsafe(32)
    db.add(LoginSession(token_hash=digest(token), user_id=user.id,
        expires_at=now()+timedelta(hours=settings.session_hours)))
    db.commit()
    response.set_cookie("game_session", token, httponly=True, secure=settings.cookie_secure,
        samesite="lax", max_age=settings.session_hours*3600, path="/")
    return {"username": user.username}


def logout(request: Request, response: Response, db: DB):
    session = db.get(LoginSession, digest(request.cookies.get("game_session", "")))
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie("game_session", path="/")
    return {"message": "로그아웃했어."}
