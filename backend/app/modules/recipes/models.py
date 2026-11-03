"""재료·결과는 모두 공통 item.id를 참조한다. 조합 기능은 추후 구현."""
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Recipe(Base):
    __tablename__ = "recipe"
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    name: Mapped[str] = mapped_column(String(100), comment='이름')
    main_item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), comment='주재료 아이템 ID')
    sub_item1_id: Mapped[int | None] = mapped_column(ForeignKey("item.id"), nullable=True, comment='첫 번째 부재료 ID')
    sub_item2_id: Mapped[int | None] = mapped_column(ForeignKey("item.id"), nullable=True, comment='두 번째 부재료 ID')
    result_item_id: Mapped[int] = mapped_column(ForeignKey("item.id"), comment='조합 결과 아이템 ID')
