"""성격 키워드와 캐릭터별 분류당 한 개의 선택을 저장한다."""
from sqlalchemy import String, Integer, ForeignKey, ForeignKeyConstraint, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ...database.base import Base


class PersonalityKeyword(Base):
    __tablename__ = 'personality_keyword'
    __table_args__ = (UniqueConstraint('id','category', name='uq_keyword_id_category'),
        CheckConstraint("category IN ('OUTER','INNER','ALIGNMENT')", name='ck_keyword_category'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='성격 키워드 ID')
    category: Mapped[str] = mapped_column(String(12), comment='분류: OUTER겉 INNER속 ALIGNMENT성향')
    code: Mapped[str] = mapped_column(String(40), unique=True, comment='성격 고유 코드')
    name: Mapped[str] = mapped_column(String(30), comment='성격 표시 이름')
    description: Mapped[str] = mapped_column(String(200), default='', server_default='', comment='성격 설명')


class CharacterPersonality(Base):
    __tablename__ = 'character_personality'
    __table_args__ = (UniqueConstraint('character_id','category', name='uq_character_category'),
        ForeignKeyConstraint(['keyword_id','category'], ['personality_keyword.id','personality_keyword.category'], name='fk_character_keyword_category'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='성격 선택 ID')
    character_id: Mapped[int] = mapped_column(ForeignKey('character.id', ondelete='CASCADE'), comment='캐릭터 ID')
    category: Mapped[str] = mapped_column(String(12), comment='선택 분류')
    keyword_id: Mapped[int] = mapped_column(Integer, comment='선택한 성격 키워드 ID')
    keyword: Mapped['PersonalityKeyword'] = relationship(lazy='joined')
