from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./game.db"
    frontend_origin: str = "http://localhost:5174"
    cookie_secure: bool = False
    session_hours: int = 24
    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
# All ranges are inclusive. Existing rolls are kept when these defaults change.
CORE_STATS = ("strength", "stamina", "intelligence", "agility", "luck")
STAT_TOTAL = 20
STAT_RANGES = {"appearance": (1, 100), "height_cm": (140, 200),
               **{key: (1, 16) for key in CORE_STATS}}
MAX_REROLLS = 10
