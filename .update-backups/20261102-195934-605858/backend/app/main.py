"""Application assembly only. Feature behavior is in modules/."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from .config import settings
from .db import Base, engine
from . import models  # Register every SQLAlchemy table before create_all.
from .modules.auth.router import router as auth_router
from .modules.characters.router import router as character_router
import logging

logger = logging.getLogger("uvicorn.error")
@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Webgame foundation", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin],
    allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def guard_origin(request: Request, call_next):
    origin = request.headers.get("origin")

    allowed_origins = {
        settings.frontend_origin.rstrip("/"),
        str(request.base_url).rstrip("/"),  # 백엔드의 Swagger 요청
    }

    if (
        request.method not in {"GET", "HEAD", "OPTIONS"}
        and origin not in allowed_origins
    ):
        logger.warning(
            "출처 차단: method=%s path=%s origin=%r allowed=%s",
            request.method,
            request.url.path,
            origin,
            sorted(allowed_origins),
        )

        return JSONResponse(
            {"detail": "허용되지 않은 요청 출처야."},
            status_code=403,
        )

    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"

    return response


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth_router)
app.include_router(character_router)
