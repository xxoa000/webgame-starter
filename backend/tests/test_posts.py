"""게시판 CRUD·공지 필터·운영 권한·정렬·소프트 삭제를 검증한다."""
import pytest
from sqlalchemy import select
from test_flow import client, auth, CREDS
from app.modules.users.models import User
from app.modules.posts.models import Post


def promote(factory, auth_value):
    """테스트 계정에 지정한 운영 권한을 부여한다."""
    with factory() as db:
        db.scalar(select(User)).auth = auth_value
        db.commit()


def test_user_crud_and_owner_guards(client):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory = client
    assert c.get('/posts').status_code == 200
    assert c.post('/posts', json={'title':'제목','content':'본문'}).status_code == 401
    auth(c)
    body = {'title':'첫 글','content':'본문'}
    assert c.post('/posts', json={**body,'username':'admin'}).status_code == 422
    assert c.post('/posts', json={**body,'is_notice':1}).status_code == 403
    first = c.post('/posts', json=body)
    assert first.status_code == 201
    post = first.json(); post_id = post['id']
    assert post['username'] == CREDS['username'] and post['is_notice'] == 0 and post['post_status'] == 1
    assert c.patch(f'/posts/{post_id}', json={'content':'수정'}).json()['content'] == '수정'
    assert c.patch(f'/posts/{post_id}', json={'post_status':1}).status_code == 403
    assert c.patch(f'/posts/{post_id}', json={'is_notice':1}).status_code == 403
    assert c.patch(f'/posts/{post_id}', json={'username':'else'}).status_code == 422
    assert c.patch(f'/posts/{post_id}', json={'title':None}).status_code == 422
    assert c.post('/posts', json={'title':'  ','content':'본문'}).status_code == 422
    assert c.get('/posts?include_inactive=true').status_code == 403
    c.post('/auth/logout', json={})
    other = {'username':'other_writer','password':CREDS['password']}
    c.post('/auth/signup', json=other); c.post('/auth/login', json=other)
    assert c.patch(f'/posts/{post_id}', json={'title':'남의 글'}).status_code == 403
    assert c.delete(f'/posts/{post_id}').status_code == 403
    c.post('/auth/logout', json={}); c.post('/auth/login', json=CREDS)
    assert c.delete(f'/posts/{post_id}').status_code == 200
    assert c.get(f'/posts/{post_id}').status_code == 404
    assert c.get('/posts').json()['total'] == 0
    with factory() as db:
        assert db.get(Post, post_id).post_status == 3


@pytest.mark.parametrize('role', [1,9])
def test_staff_admin_notices_and_status_visibility(client, role):
    """해당 기능의 정상 동작과 예외 조건을 검증한다."""
    c, factory = client
    auth(c); promote(factory, role)
    posts = []
    for n in range(5):
        response = c.post('/posts', json={'title':f'글{n}','content':'내용', 'is_notice':n % 2})
        assert response.status_code == 201
        posts.append(response.json())
    assert [p['id'] for p in c.get('/posts').json()['items']] == [p['id'] for p in reversed(posts)]
    for status in [0,2,3]:
        assert c.patch(f"/posts/{posts[status]['id']}", json={'post_status':status}).status_code == 200
    visible = c.get('/posts').json()
    assert all(p['post_status'] == 1 for p in visible['items'])
    assert c.get('/posts?include_inactive=true').json()['total'] == 5
    c.post('/auth/logout', json={})
    notices = c.get('/posts/notices').json()['items']
    assert all(p['post_status'] == 1 and p['is_notice'] == 1 for p in notices)
    assert c.get(f"/posts/{posts[0]['id']}").status_code == 404
    assert c.get('/posts?page=0').status_code == 422
    assert c.get('/posts?page_size=101').status_code == 422
    assert len(c.get('/posts?page_size=1').json()['items']) == 1
