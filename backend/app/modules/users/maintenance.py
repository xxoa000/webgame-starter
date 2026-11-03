"""달력 기준 3개월 미접속 계정을 매일 휴면으로 전환한다."""
import asyncio
import calendar
import logging
from datetime import timedelta
from sqlalchemy import select, update, func
from ...database.session import SessionLocal
from ...database.base import utc_now
from .models import User

logger = logging.getLogger('uvicorn.error')


def three_months_after(value):
    """월말을 보정해 기준 시각에 달력상 3개월을 더한다."""
    month_index = value.year * 12 + value.month - 1 + 3
    year, month = divmod(month_index, 12)
    month += 1
    return value.replace(year=year, month=month, day=min(value.day, calendar.monthrange(year, month)[1]))


def mark_dormant(db, at=None):
    """로그인 경합을 검사하며 활성 계정만 휴면으로 바꾼다."""
    at = at or utc_now()
    count = 0
    anchor = func.coalesce(User.last_login_at, User.create_at)
    rows = db.execute(select(User.id, anchor.label('anchor')).where(User.user_status == 1,
        anchor <= at - timedelta(days=89))).all()
    for user_id, previous in rows:
        if three_months_after(previous) <= at:
            result = db.execute(update(User).where(User.id == user_id, User.user_status == 1,
                anchor == previous).values(user_status=0))
            count += result.rowcount
    db.commit()
    return count


def run_daily():
    """독립 세션에서 하루 분량의 휴면 정리를 실행한다."""
    with SessionLocal() as db:
        return mark_dormant(db)


async def daily_loop():
    """서버 시작 시와 이후 매일 UTC 자정에 휴면 작업을 실행한다."""
    while True:
        try:
            await asyncio.to_thread(run_daily)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('휴면 계정 정리에 실패했습니다.')
        current = utc_now()
        midnight = (current + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep(max(1, (midnight-current).total_seconds()))
