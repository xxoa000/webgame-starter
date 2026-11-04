"""영구 확장 상품의 이름과 운영 가격을 저장한다."""
from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class ShopUpgrade(Base):
    """가방 확장·스탯 포인트 상품. 효과는 서버의 code 분기로 검증한다."""
    __tablename__ = 'shop_upgrade'
    __table_args__ = (CheckConstraint('price > 0', name='ck_shop_upgrade_price'),)
    code: Mapped[str] = mapped_column(String(32), primary_key=True, comment='영구 상품 코드')
    name: Mapped[str] = mapped_column(String(80), comment='상품 이름')
    description: Mapped[str] = mapped_column(String(200), comment='상품 효과 안내')
    price: Mapped[int] = mapped_column(Integer, comment='개당 구매 가격(C)')
