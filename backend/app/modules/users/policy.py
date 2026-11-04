"""계정 이용 상태와 운영 권한을 구분하여 검사한다."""
from fastapi import HTTPException
USER, STAFF, ADMIN = 0, 1, 9
INACTIVE, ACTIVE, SANCTIONED, WITHDRAW = 0, 1, 2, 3


def ensure_active(user):
    """활성 계정의 기존 JWT만 허용한다."""
    if user.user_status != ACTIVE:
        raise HTTPException(403, '다시 로그인하거나 계정 상태를 확인해.')


def is_staff(user):
    """스탭 또는 관리자 권한인지 판정한다."""
    return user.auth in (STAFF, ADMIN)


def require_staff(user):
    """운영 권한이 없는 계정의 관리 요청을 차단한다."""
    if not is_staff(user):
        raise HTTPException(403, '운영 권한이 필요해.')
