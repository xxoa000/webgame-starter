from typing import Annotated
from fastapi import APIRouter, Request, Response
from pydantic import Field
from ...core.dependencies import DB
from .schemas import Credentials
from . import repository, service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/check-username")
def check_username(username: Annotated[str, Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")], db: DB):
    return {"available": repository.find_by_username(db, username.lower()) is None}


@router.post("/signup", status_code=201)
def signup(body: Credentials, db: DB):
    return service.signup(body, db)


@router.post("/login")
def login(body: Credentials, response: Response, db: DB):
    return service.login(body, response, db)


@router.post("/logout")
def logout(request: Request, response: Response, db: DB):
    return service.logout(request, response, db)
