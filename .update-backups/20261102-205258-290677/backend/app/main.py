"""앱 생성과 라우터 등록. 기능 구현은 modules/ 아래에 둔다."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from .core.config import settings
from .database.checks import assert_schema_current
from .modules.users.router import router as users_router
from .modules.characters.router import router as characters_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app):
    assert_schema_current()
    yield


app = FastAPI(title="Webgame foundation", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin.rstrip("/")],
    allow_credentials=True, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def guard_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    allowed = {settings.frontend_origin.rstrip("/"), str(request.base_url).rstrip("/")}
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin not in allowed:
        logger.warning("출처 차단: method=%s path=%s origin=%r allowed=%s",
            request.method, request.url.path, origin, sorted(allowed))
        return JSONResponse({"detail": "허용되지 않은 요청 출처야."}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(characters_router)
# posts.router는 실제 API 구현 후 등록한다.
