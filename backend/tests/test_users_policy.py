"""권한 주입 차단·휴면 전환·재활성화·기존 세션 차단을 검증한다."""
from datetime import datetime, timedelta
import pytest
from sqlalchemy import select
from test_flow import client, auth, CREDS
from app.modules.users.models import User
from app.modules.users.maintenance import mark_dormant, three_months_after


def test_signup_defaults_and_privilege_injection(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory = client
    assert c.post('/auth/signup', json={**CREDS, 'auth':9}).status_code == 422
    auth(c)
    with factory() as db:
        user = db.scalar(select(User))
        assert user.auth == 0 and user.user_status == 1 and user.last_login_at is not None
        assert user.create_at and user.update_at
    assert c.get('/me').json()['auth'] == 0


@pytest.mark.parametrize('status', [2,3])
def test_sanctioned_and_withdrawn_sessions_block(client, status):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory = client
    auth(c)
    with factory() as db:
        user = db.scalar(select(User)); before = user.last_login_at
        user.user_status = status; db.commit()
    assert c.get('/me').status_code == 403
    assert c.post('/posts', json={'title':'제목','content':'본문'}).status_code == 403
    assert c.post('/auth/login', json=CREDS).status_code == 403
    with factory() as db:
        assert db.scalar(select(User)).last_login_at == before


def test_calendar_dormancy_and_reactivation(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory = client
    auth(c)
    cutoff = datetime(2026,4,30,12)
    with factory() as db:
        user = db.scalar(select(User)); user.last_login_at = datetime(2026,1,31,12)
        db.commit()
        assert mark_dormant(db, cutoff - timedelta(seconds=1)) == 0
        assert mark_dormant(db, cutoff) == 1
        assert mark_dormant(db, cutoff) == 0
    assert c.get('/me').status_code == 403
    assert c.post('/auth/login', json={**CREDS,'password':'wrong-password'}).status_code == 401
    with factory() as db:
        assert db.scalar(select(User)).user_status == 0
    assert c.post('/auth/login', json=CREDS).status_code == 200
    assert c.get('/me').json()['user_status'] == 1


def test_no_login_uses_creation_and_excludes_sanctioned(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    _, factory = client
    with factory() as db:
        db.add_all([User(username=f'never_{n}', password_hash='hash', user_status=n,
            create_at=datetime(2025,1,1)) for n in (1,2,3)])
        db.commit()
        assert mark_dormant(db, datetime(2026,1,1)) == 1
        states = dict(db.execute(select(User.username,User.user_status)).all())
        assert states == {'never_1':0,'never_2':2,'never_3':3}
    assert three_months_after(datetime(2023,11,30)).date() == datetime(2024,2,29).date()
