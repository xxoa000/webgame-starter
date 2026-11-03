"""요청 입력과 응답 데이터 형식을 검증한다."""
from pydantic import BaseModel, Field, field_validator

class Credentials(BaseModel):
    model_config = {"extra": "forbid"}
    username: str = Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")
    password: str = Field(min_length=10, max_length=128)
    @field_validator("username")
    @classmethod
    def normalize(cls, value):
        """로그인 아이디를 소문자로 정규화한다."""
        return value.lower()
