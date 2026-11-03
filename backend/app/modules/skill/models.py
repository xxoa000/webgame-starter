"""스킬북 데이터 정의. 스킬 습득·사용 기능은 아직 구현하지 않는다."""
from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class Skill(Base):
    __tablename__ = "skill"
    __table_args__ = (CheckConstraint("power >= 0", name="ck_skill_power"),
                      CheckConstraint("mana_cost >= 0", name="ck_skill_mana"))
    id: Mapped[int] = mapped_column(primary_key=True, comment='고유 ID')
    skill_name: Mapped[str] = mapped_column(String(100), comment='스킬 이름')
    description: Mapped[str] = mapped_column(Text, comment='설명')
    power: Mapped[int] = mapped_column(comment='스킬 위력')
    mana_cost: Mapped[int] = mapped_column(comment='필요 MP')
