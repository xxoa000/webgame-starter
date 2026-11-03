import hashlib
import secrets
from datetime import datetime, timezone
from typing import Annotated
from fastapi import Depends, HTTPException, Request
from pwdlib import PasswordHash
from .dependencies import DB
from ..modules.auth.models import LoginSession, User

hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("dummy-password-for-timing")

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def current_user(request: Request, db: DB):
    token = request.cookies.get("game_session", "")
    session = db.get(LoginSession, digest(token)) if token else None
    if not session or session.expires_at <= now():
        raise HTTPException(401, "로그인이 필요해.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "로그인이 필요해.")
    return user

Auth = Annotated[User, Depends(current_user)]
