"""초기 성격 키워드 조회 API를 제공한다."""
from fastapi import APIRouter
from ...core.dependencies import DB
from .service import choices

router = APIRouter(prefix='/personality', tags=['personality'])


@router.get('/keywords')
def keywords(db: DB):
    """캐릭터 생성 화면에 분류별 키워드 목록을 제공한다."""
    return [{'id':row.id,'category':row.category,'code':row.code,'name':row.name,'description':row.description} for row in choices(db)]
