"""환경 설정 값을 검증하고 읽어온다."""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./game.db"
    frontend_origin: str = "http://localhost:5174"
    cookie_secure: bool = False
    session_hours: int = 24
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
