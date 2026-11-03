"""게시글 공개 조건·내림차순 정렬·페이지네이션과 잠금 조회를 담당한다."""
from sqlalchemy import select, func
from .models import Post


def list_page(db, page, page_size, notices=False, include_inactive=False):
    """일반 조회는 활성 글만 최신 생성 순서로 반환한다."""
    conditions = [] if include_inactive else [Post.post_status == 1]
    if notices:
        conditions.append(Post.is_notice == 1)
    total = db.scalar(select(func.count()).select_from(Post).where(*conditions))
    rows = db.scalars(select(Post).where(*conditions).order_by(Post.create_at.desc(), Post.id.desc())
        .offset((page-1)*page_size).limit(page_size)).all()
    return {'items': rows, 'total': total, 'page': page, 'page_size': page_size}


def get(db, post_id, lock=False):
    """게시글을 조회하고 변경 시에는 행 잠금을 획득한다."""
    statement = select(Post).where(Post.id == post_id)
    if lock:
        statement = statement.with_for_update()
    return db.scalar(statement)
