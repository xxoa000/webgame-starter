"""게시글 작성·수정 입력과 목록·상세 응답을 검증한다."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class PostCreate(BaseModel):
    """작성자와 권한을 입력받지 않는 게시글 작성 요청이다."""
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=16000)
    is_notice: int = Field(default=0, ge=0, le=1, strict=True)

    @field_validator('title','content')
    @classmethod
    def not_blank(cls, value):
        """공백으로만 구성된 제목과 본문을 거부한다."""
        if not value.strip():
            raise ValueError('제목과 본문을 입력해.')
        return value.strip()


class PostUpdate(BaseModel):
    """명시적으로 전달한 필드만 갱신하는 요청이다."""
    model_config = ConfigDict(extra='forbid')
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1, max_length=16000)
    is_notice: int | None = Field(default=None, ge=0, le=1, strict=True)
    post_status: int | None = Field(default=None, ge=0, le=3, strict=True)

    @field_validator('title','content','is_notice','post_status', mode='before')
    @classmethod
    def reject_null(cls, value):
        """전달한 필드에 NULL이나 빈 문자열을 저장하지 못하게 한다."""
        if value is None or isinstance(value, str) and not value.strip():
            raise ValueError('빈 값으로 변경할 수 없어.')
        return value.strip() if isinstance(value, str) else value


class PostResponse(BaseModel):
    """저장된 게시글과 감사 시각을 응답한다."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    content: str
    username: str
    is_notice: int
    post_status: int
    create_at: datetime
    update_at: datetime


class PostPage(BaseModel):
    """페이지 번호와 전체 건수를 포함한 게시글 목록이다."""
    items: list[PostResponse]
    total: int
    page: int
    page_size: int
