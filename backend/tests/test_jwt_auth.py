"""JWT 검증·권한·로그아웃 무효화와 마이그레이션을 검증한다."""
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from pydantic import SecretStr
from sqlalchemy import select, create_engine, text, inspect
from alembic.migration import MigrationContext
from alembic.operations import Operations
from test_flow import client, auth, CREDS
from app.core.config import settings, Settings
from app.core.security import ACCESS_COOKIE, decode_access_token
from app.modules.users.models import User


def signed(claims):
    """검증 실패 조건을 격리하기 위해 테스트 JWT를 서명한다."""
    return jwt.encode(claims, settings.signing_key(), algorithm='HS256')


def test_cookie_and_logout(client):
    """JWT 쿠키 설정과 복사한 토큰까지 무효화되는지 검증한다."""
    c, factory = client
    auth(c)
    first = c.cookies.get(ACCESS_COOKIE)
    claims = decode_access_token(first)
    assert first.count('.') == 2 and claims['sub'] == '1' and claims['ver'] == 0
    assert claims['exp'] - claims['iat'] == 86400
    assert 'auth' not in claims and 'password_hash' not in claims
    response = c.post('/auth/login', json=CREDS)
    assert any('game_access=' in v and 'HttpOnly' in v and 'SameSite=lax' in v for v in response.headers.get_list('set-cookie'))
    second = c.cookies.get(ACCESS_COOKIE)
    assert second != first
    assert c.post('/auth/logout').status_code == 200
    assert c.get('/me').status_code == 401
    for token in (first, second):
        c.cookies.clear(); c.cookies.set(ACCESS_COOKIE, token)
        assert c.get('/me').status_code == 401
    assert c.post('/auth/logout').status_code == 200
    with factory() as db: assert db.scalar(select(User)).token_version == 1
    c.cookies.clear()
    assert c.post('/auth/login', json=CREDS).status_code == 200
    assert decode_access_token(c.cookies.get(ACCESS_COOKIE))['ver'] == 1
    assert c.get('/me').status_code == 200


@pytest.mark.parametrize('case', ['expired','future','issuer','audience','subject','version','type','missing','signature','none','malformed'])
def test_invalid_jwt(client, case):
    """만료·위조·잘못된 클레임·알고리즘 우회를 거부한다."""
    c, _ = client
    auth(c)
    claims = decode_access_token(c.cookies.get(ACCESS_COOKIE))
    if case == 'expired': claims['exp'] = int((datetime.now(timezone.utc)-timedelta(seconds=1)).timestamp())
    elif case == 'future': claims['nbf'] = int((datetime.now(timezone.utc)+timedelta(hours=1)).timestamp())
    elif case == 'issuer': claims['iss'] = 'wrong'
    elif case == 'audience': claims['aud'] = 'wrong'
    elif case == 'subject': claims['sub'] = 'not-an-id'
    elif case == 'version': claims['ver'] = True
    elif case == 'type': claims['token_type'] = 'refresh'
    elif case == 'missing': del claims['exp']
    token = signed(claims)
    if case == 'signature': token = jwt.encode(claims, 'wrong-key-with-at-least-32-bytes-1234567890', algorithm='HS256')
    elif case == 'none': token = jwt.encode(claims, '', algorithm='none')
    elif case == 'malformed': token = 'not-a-jwt'
    c.cookies.clear(); c.cookies.set(ACCESS_COOKIE, token)
    assert c.get('/me').status_code == 401
    assert c.post('/characters/draft', json={}).status_code == 401


def test_live_db_role(client):
    """JWT를 재발급하지 않아도 DB 권한 변경이 반영되는지 검증한다."""
    c, factory = client
    auth(c)
    token = c.cookies.get(ACCESS_COOKIE)
    for role in (0,1,9,0):
        with factory() as db:
            db.scalar(select(User)).auth = role; db.commit()
        assert c.get('/me').json()['auth'] == role
        assert c.get('/posts?include_inactive=true').status_code == (200 if role in (1,9) else 403)
        assert c.cookies.get(ACCESS_COOKIE) == token
    claims = decode_access_token(token); claims['auth'] = 9
    c.cookies.clear(); c.cookies.set(ACCESS_COOKIE, signed(claims))
    assert c.get('/posts?include_inactive=true').status_code == 403


def test_old_cookie_and_origin(client):
    """세션 쿠키를 인증에 사용하지 않고 기존 출처 방어를 유지한다."""
    c, _ = client
    auth(c)
    token = c.cookies.get(ACCESS_COOKIE)
    c.cookies.clear(); c.cookies.set('game_session', token)
    assert c.get('/me').status_code == 401
    c.cookies.set(ACCESS_COOKIE, token)
    assert c.post('/auth/logout', headers={'Origin':'https://evil.example'}).status_code == 403
    assert c.get('/me').status_code == 200


def test_no_default_key():
    """키 누락·짧은 키를 거부하고 고정 기본키로 대체하지 않는다."""
    for key in ('','short'):
        with pytest.raises(RuntimeError):
            Settings(_env_file=None, jwt_secret_key=SecretStr(key)).signing_key()


def test_migration():
    """0016 적용·되돌리기에서 사용자 보존과 세션 폐기를 확인한다."""
    spec = importlib.util.spec_from_file_location('jwt_revision', Path(__file__).resolve().parents[1]/'alembic/versions/0016_jwt_auth.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    engine = create_engine('sqlite://')
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE users (id INTEGER PRIMARY KEY, username VARCHAR(24))'))
        connection.execute(text("INSERT INTO users VALUES (1,'preserved')"))
        connection.execute(text('CREATE TABLE login_session (token_hash VARCHAR(64) PRIMARY KEY, user_id INTEGER, expires_at DATETIME)'))
        connection.execute(text("INSERT INTO login_session VALUES ('old-token',1,'2099-01-01')"))
        with Operations.context(MigrationContext.configure(connection)):
            module.upgrade()
            assert connection.execute(text('SELECT username,token_version FROM users')).one() == ('preserved',0)
            assert 'login_session' not in inspect(connection).get_table_names()
            module.downgrade()
            assert connection.execute(text('SELECT username FROM users')).scalar() == 'preserved'
            assert connection.execute(text('SELECT COUNT(*) FROM login_session')).scalar() == 0
