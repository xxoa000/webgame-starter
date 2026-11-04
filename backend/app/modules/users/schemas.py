""" 요청 입력과 응답 데이터 형식을 검증한다. """

from pydantic import BaseModel, Field, field_validator

class Credentials(BaseModel):
    model_config = {"extra": "forbid"}
    # model_config: 이 모델의 동작 설정
        # extra: 정의하지 않은 추가 필드 값이 들어올 경우의 처리 방식
            # forbid: 추가 필드를 허용하지 않음
            # ignore: 추가 필드를 무시하고 나머지는 처리. (기본값)
            # allow: 	추가 필드도 모델에 보관

    username: str = Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")
    password: str = Field(min_length=10, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize(cls, value):
        """ 로그인 아이디를 소문자로 정규화한다. """
        return value.lower()
