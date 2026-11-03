"""앱 생성과 라우터 등록. 기능 구현은 modules/ 아래에 둔다."""
import logging
import asyncio
from contextlib import suppress
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from .core.config import settings
from .database import metadata as _metadata  # Register the complete FK graph.
from .database.checks import assert_schema_current
from .modules.users.router import router as users_router
from .modules.characters.router import router as characters_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app):
    """기동 시 DB 상태를 확인하고 주기 작업의 수명을 관리한다."""
    assert_schema_current()
    from .modules.users.maintenance import daily_loop
    task = asyncio.create_task(daily_loop())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(title="Webgame foundation", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin.rstrip("/")],
    allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE"], allow_headers=["Content-Type"])


@app.middleware("http")
async def guard_origin(request: Request, call_next):
    """요청 출처를 검증하고 공통 응답 헤더를 설정한다."""
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
    """서버의 기본 응답 상태를 반환한다."""
    return {"status": "ok"}


app.include_router(users_router)
app.include_router(characters_router)
from .modules.posts.router import router as posts_router
app.include_router(posts_router)

# New gameplay modules; existing users/characters routes remain unchanged.
from .modules.inventory.router import router as inventory_router
from .modules.exploration.router import router as exploration_router
from .modules.maps.router import router as maps_router
app.include_router(inventory_router)
app.include_router(exploration_router)
app.include_router(maps_router)

from .modules.encyclopedia.router import router as encyclopedia_router
app.include_router(encyclopedia_router)

from .modules.personality.router import router as personality_router
app.include_router(personality_router)
