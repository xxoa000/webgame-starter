"""게시글 목록·공지·상세·작성·수정·삭제 API를 연결한다."""
from typing import Annotated
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from ...core.dependencies import DB
from ...core.security import ACCESS_COOKIE, Auth, current_user
from .schemas import PostCreate, PostUpdate, PostResponse, PostPage
from . import service

router = APIRouter(prefix='/posts', tags=['posts'])


def optional_user(request: Request, db: DB):
    """비로그인 조회를 허용하되 운영 권한은 유효한 JWT에서만 가져온다."""
    if not request.cookies.get(ACCESS_COOKIE):
        return None
    try:
        return current_user(request, db)
    except HTTPException as error:
        if error.status_code == 401:
            return None
        raise


Viewer = Annotated[object, Depends(optional_user)]


@router.get('', response_model=PostPage)
def list_posts(db: DB, user: Viewer, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), include_inactive: bool = False):
    """활성 글의 최신순 목록이나 권한 있는 운영 목록을 반환한다."""
    return service.list_posts(db, user, page, page_size, include_inactive=include_inactive)


@router.get('/notices', response_model=PostPage)
def notices(db: DB, user: Viewer, page: int = Query(1, ge=1), page_size: int = Query(5, ge=1, le=100)):
    """홈에 표시할 활성 공지만 반환한다."""
    return service.list_posts(db, user, page, page_size, notices=True)


@router.get('/{post_id}', response_model=PostResponse)
def detail(post_id: int, db: DB, user: Viewer):
    """조회 권한을 확인한 게시글 본문을 반환한다."""
    return service.detail(db, user, post_id)


@router.post('', response_model=PostResponse, status_code=201)
def create(body: PostCreate, db: DB, user: Auth):
    """로그인 사용자의 게시글을 작성한다."""
    return service.create(db, user, body)


@router.patch('/{post_id}', response_model=PostResponse)
def update(post_id: int, body: PostUpdate, db: DB, user: Auth):
    """본인 또는 운영 권한으로 게시글을 수정한다."""
    return service.update(db, user, post_id, body)


@router.delete('/{post_id}')
def delete(post_id: int, db: DB, user: Auth):
    """게시글을 삭제 상태로 변경한다."""
    return service.delete(db, user, post_id)
