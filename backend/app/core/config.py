"""환경 설정 값을 검증하고 읽어온다."""
from pydantic_settings import BaseSettings
from pydantic import Field, SecretStr

class Settings(BaseSettings):
    database_url: str = "sqlite:///./game.db"
    frontend_origin: str = "http://localhost:5174"
    cookie_secure: bool = False
    jwt_secret_key: SecretStr = SecretStr("")
    jwt_access_hours: int = Field(default=24, ge=1, le=168)
    model_config = {"env_file": ".env", "extra": "ignore"}

    def signing_key(self) -> str:
        """고정 기본키 없이 운영자가 제공한 JWT 서명키를 검증한다."""
        key = self.jwt_secret_key.get_secret_value()
        if len(key.encode("utf-8")) < 32:
            raise RuntimeError("JWT_SECRET_KEY에 무작위로 생성한 32바이트 이상의 서명키를 설정해.")
        return key

settings = Settings()
