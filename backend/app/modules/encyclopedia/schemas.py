"""요청 입력과 응답 데이터 형식을 검증한다."""
# 도감과 지도 미리보기는 같은 공개 데이터 형식을 공유한다.
from ..maps.schemas import MapResponse

__all__=['MapResponse']
