from pydantic import BaseModel, Field, field_validator

class Credentials(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z0-9_]{4,24}$")
    password: str = Field(min_length=10, max_length=128)
    @field_validator("username")
    @classmethod
    def normalize(cls, value):
        return value.lower()
