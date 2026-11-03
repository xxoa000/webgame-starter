import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .config import settings, STAT_RANGES, MAX_REROLLS, CORE_STATS, STAT_TOTAL
from .db import Base, engine, get_db
from .names import clean_name, name_key
from .models import User, LoginSession, Character, DeletedCharacter

@asynccontextmanager
async def lifespan(app):
    # Bootstrap only. Introduce Alembic migrations before changing an existing schema.
    Base.metadata.create_all(engine)
    yield

app = FastAPI(title="Webgame foundation", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin],
    allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.middleware("http")
async def guard_origin(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("origin") != settings.frontend_origin:
        from starlette.responses import JSONResponse
        return JSONResponse({"detail": "허용되지 않은 요청 출처야."}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

DB = Annotated[Session, Depends(get_db)]
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

class Credentials(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")
    password: str = Field(min_length=10, max_length=128)
    @field_validator("username")
    @classmethod
    def normalize(cls, value):
        return value.lower()

class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=24)
    gender: Literal["male", "female", "other"]
    age: int = Field(ge=10, le=17, strict=True)
    bio: str = Field(default="", max_length=500)
    @field_validator("name")
    @classmethod
    def trim(cls, value):
        if not value.strip():
            raise ValueError("이름을 입력해.")
        return clean_name(value)

def character_data(c):
    if not c:
        return None
    return {"id": c.id, "name": c.name, "gender": c.gender, "age": c.age, "bio": c.bio,
            "stats": c.stats, "status": c.status, "rerolls_used": c.rerolls,
            "rerolls_remaining": MAX_REROLLS-c.rerolls}

def roll():
    # Uniformly sample positive integer compositions of 20 into five parts.
    cuts = [0, *sorted(secrets.SystemRandom().sample(range(1, STAT_TOTAL), len(CORE_STATS)-1)), STAT_TOTAL]
    stats = {key: cuts[i+1]-cuts[i] for i, key in enumerate(CORE_STATS)}
    stats.update({key: low + secrets.randbelow(high-low+1)
                  for key, (low, high) in STAT_RANGES.items() if key not in CORE_STATS})
    return stats

def owned_character(db, user):
    # Every creation mutation first locks the same parent row, including first roll.
    db.execute(select(User).where(User.id == user.id).with_for_update()).scalar_one()
    return db.scalar(select(Character).where(Character.user_id == user.id).with_for_update())

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/auth/check-username")
def check_username(username: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")], db: DB):
    return {"available": db.scalar(select(User.id).where(User.username == username.lower())) is None}

@app.post("/auth/signup", status_code=201)
def signup(body: Credentials, db: DB):
    if db.scalar(select(User.id).where(User.username == body.username)):
        raise HTTPException(409, "이미 사용 중인 아이디야.")
    db.add(User(username=body.username, password_hash=hasher.hash(body.password)))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용 중인 아이디야.")
    return {"message": "가입 완료. 로그인해."}

@app.post("/auth/login")
def login(body: Credentials, response: Response, db: DB):
    user = db.scalar(select(User).where(User.username == body.username))
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

@app.post("/auth/logout")
def logout(request: Request, response: Response, db: DB):
    session = db.get(LoginSession, digest(request.cookies.get("game_session", "")))
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie("game_session", path="/")
    return {"message": "로그아웃했어."}

@app.get("/me")
def me(user: Auth, db: DB):
    return {"username": user.username, "character": character_data(db.scalar(
        select(Character).where(Character.user_id == user.id)))}

@app.get("/characters/rules")
def rules():
    return {"ranges": STAT_RANGES, "max_rerolls": MAX_REROLLS, "stat_total": STAT_TOTAL}

@app.post("/characters/draft")
def draft(user: Auth, db: DB):
    c = owned_character(db, user)
    if not c:
        c = Character(user_id=user.id, stats=roll(), rerolls=0, status="draft")
        db.add(c)
        db.commit()
    return character_data(c)

@app.post("/characters/reroll")
def reroll(user: Auth, db: DB):
    c = owned_character(db, user)
    if not c or c.status != "draft":
        raise HTTPException(409, "재추첨할 생성 중 캐릭터가 없어.")
    if c.rerolls >= MAX_REROLLS:
        raise HTTPException(409, "재추첨 10회를 모두 사용했어.")
    c.stats = roll()
    c.rerolls += 1
    db.commit()
    return character_data(c)

@app.post("/characters/finalize")
def finalize(body: Profile, user: Auth, db: DB):
    c = owned_character(db, user)
    if not c or c.status != "draft":
        raise HTTPException(409, "확정할 생성 중 캐릭터가 없어.")
    key = name_key(body.name)
    if db.scalar(select(Character.id).where(Character.name_key == key)) is not None:
        raise HTTPException(409, "이미 사용 중인 캐릭터 이름이야.")
    c.name, c.name_key = body.name, key
    c.gender, c.age, c.bio, c.status = body.gender, body.age, body.bio, "ready"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용 중인 캐릭터 이름이야. 다시 확인해.")
    return character_data(c)


@app.get("/characters/check-name")
def check_character_name(name: Annotated[str, Field(min_length=1, max_length=24)], user: Auth, db: DB):
    if not clean_name(name):
        raise HTTPException(422, "이름을 입력해.")
    return {"available": db.scalar(select(Character.id).where(Character.name_key == name_key(name))) is None}


class DeleteCharacterRequest(BaseModel):
    character_id: int = Field(gt=0, strict=True)
    name: str = Field(min_length=1, max_length=24)


@app.post("/characters/delete")
def delete_character(body: DeleteCharacterRequest, user: Auth, db: DB):
    c = owned_character(db, user)
    if not c or c.id != body.character_id:
        raise HTTPException(404, "삭제할 캐릭터를 찾을 수 없어. 화면을 새로고침해.")
    if c.status != "ready":
        raise HTTPException(409, "생성이 완료된 캐릭터만 삭제할 수 있어.")
    # Confirmation must match the displayed name exactly, including case/spaces.
    if body.name != c.name:
        raise HTTPException(422, "캐릭터 이름이 일치하지 않아.")
    archive = DeletedCharacter(original_character_id=c.id, user_id=c.user_id,
        name=c.name, gender=c.gender, age=c.age, bio=c.bio, stats=dict(c.stats),
        rerolls=c.rerolls, status=c.status, deleted_at=now())
    db.add(archive)
    db.flush()  # Do not remove the live row if the archive cannot be inserted.
    db.delete(c)
    db.commit()  # Archive insertion and live deletion commit atomically.
    return {"message": "캐릭터를 삭제했어."}
