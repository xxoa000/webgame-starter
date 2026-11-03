"""게시글 소유권·공지 운영 권한·공개 상태와 소프트 삭제를 검사한다."""
from fastapi import HTTPException
from ..users.policy import is_staff, require_staff
from .models import Post
from . import repository


def list_posts(db, user, page, page_size, notices=False, include_inactive=False):
    """운영 조회가 아니면 활성 게시글만 노출한다."""
    if include_inactive:
        if user is None:
            raise HTTPException(401, '로그인이 필요해.')
        require_staff(user)
    return repository.list_page(db, page, page_size, notices, include_inactive)


def detail(db, user, post_id):
    """숨김·제재·삭제 글은 운영자 이외에 노출하지 않는다."""
    post = repository.get(db, post_id)
    if not post or (post.post_status != 1 and not (user and is_staff(user))):
        raise HTTPException(404, '게시글을 찾을 수 없어.')
    return post


def create(db, user, body):
    """작성자와 기본 상태를 서버에서 결정해 게시글을 생성한다."""
    if body.is_notice:
        require_staff(user)
    post = Post(title=body.title, content=body.content, username=user.username,
        is_notice=body.is_notice, post_status=1)
    db.add(post)
    db.commit()
    return post


def owned_post(db, user, post_id):
    """일반 사용자는 본인의 활성 일반 글만 변경하게 한다."""
    post = repository.get(db, post_id, lock=True)
    if not post:
        raise HTTPException(404, '게시글을 찾을 수 없어.')
    if not is_staff(user) and (post.username != user.username or post.is_notice or post.post_status != 1):
        raise HTTPException(403, '게시글 변경 권한이 없어.')
    return post


def update(db, user, post_id, body):
    """역할 검증 후 명시된 필드만 수정한다."""
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(422, '변경할 내용을 입력해.')
    post = owned_post(db, user, post_id)
    if 'post_status' in fields or 'is_notice' in fields:
        require_staff(user)
    for key, value in fields.items():
        setattr(post, key, value)
    db.commit()
    return post


def delete(db, user, post_id):
    """실제 행을 유지하고 삭제 상태로 전환한다."""
    post = owned_post(db, user, post_id)
    post.post_status = 3
    db.commit()
    return {'message': '게시글을 삭제했어.'}
