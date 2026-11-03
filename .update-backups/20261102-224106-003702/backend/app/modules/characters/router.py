from typing import Annotated
from fastapi import APIRouter, HTTPException
from pydantic import Field
from ...core.dependencies import DB
from ...core.security import Auth
from .rules import STAT_RANGES, MAX_REROLLS, STAT_TOTAL
from .names import clean_name, name_key
from .schemas import Profile, DeleteCharacterRequest, character_data
from . import repository, service

router = APIRouter(tags=["characters"])


@router.get("/me")
def me(user: Auth, db: DB):
    return {"username": user.username, "character": character_data(repository.get_owned(db, user.id))}


@router.get("/characters/rules")
def rules():
    return {"ranges": STAT_RANGES, "max_rerolls": MAX_REROLLS, "stat_total": STAT_TOTAL}


@router.get("/characters/check-name")
def check_name(name: Annotated[str, Field(min_length=1, max_length=24)], user: Auth, db: DB):
    if not clean_name(name):
        raise HTTPException(422, "이름을 입력해.")
    return {"available": not repository.name_exists(db, name_key(name))}


@router.post("/characters/draft")
def draft(user: Auth, db: DB):
    return service.draft(user, db)


@router.post("/characters/reroll")
def reroll(user: Auth, db: DB):
    return service.reroll(user, db)


@router.post("/characters/finalize")
def finalize(body: Profile, user: Auth, db: DB):
    return service.finalize(body, user, db)


@router.post("/characters/delete")
def delete(body: DeleteCharacterRequest, user: Auth, db: DB):
    return service.delete_character(body, user, db)
