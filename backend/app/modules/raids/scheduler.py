"""서버가 켜져 있는 동안 다음 균열의 개설 시각을 주기적으로 확인한다."""
import asyncio
import logging
from ...database.session import SessionLocal
from .service import ensure_event

logger = logging.getLogger('uvicorn.error')


def tick():
    """웹 요청과 같은 전역 잠금을 사용해 이벤트를 중복 개설하지 않는다."""
    with SessionLocal() as db:
        ensure_event(db)
        db.commit()


async def event_loop():
    """초기 웹 요청은 즉시 확인하고 백그라운드는 30초마다 일정을 갱신한다."""
    while True:
        await asyncio.sleep(30)
        try:
            await asyncio.to_thread(tick)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('균열 이벤트 일정 갱신에 실패했습니다.')
