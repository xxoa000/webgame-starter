"""요청 처리에 사용할 공통 의존성을 정의한다."""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db

DB = Annotated[Session, Depends(get_db)]
