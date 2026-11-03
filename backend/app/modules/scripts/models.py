"""공통·개인 스크립트의 버전·조건·심사·사용권을 분리하여 저장한다."""
from sqlalchemy import String, Text, Integer, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from ...database.base import Base


class ScriptPack(Base):
    __tablename__ = 'script_pack'
    __table_args__ = (CheckConstraint("kind IN ('COMMON','PERSONAL','MARKET')", name='ck_pack_kind'),)
    id: Mapped[int] = mapped_column(primary_key=True, comment='스크립트 묶음 ID')
    code: Mapped[str] = mapped_column(String(80), unique=True, comment='묶음 고유 코드')
    title: Mapped[str] = mapped_column(String(100), comment='묶음 제목')
    author_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, comment='작성자 ID, 시스템 시드는 NULL')
    kind: Mapped[str] = mapped_column(String(12), comment='종류: COMMON공통 PERSONAL개인 MARKET판매예정')


class ScriptPackVersion(Base):
    __tablename__ = 'script_pack_version'
    __table_args__ = (UniqueConstraint('pack_id','version', name='uq_pack_version'),
        CheckConstraint('version > 0', name='ck_pack_version_positive'),
        CheckConstraint("status IN ('DRAFT','PENDING','APPROVED','DISABLED')", name='ck_pack_version_status'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='묶음 버전 ID')
    pack_id: Mapped[int] = mapped_column(ForeignKey('script_pack.id'), comment='원본 묶음 ID')
    version: Mapped[int] = mapped_column(Integer, comment='버전 번호')
    status: Mapped[str] = mapped_column(String(12), default='DRAFT', server_default='DRAFT', comment='초안·심사·승인·비활성 상태')


class GameScript(Base):
    __tablename__ = 'game_script'
    __table_args__ = (CheckConstraint("layer IN ('SPEECH','THOUGHT','NARRATION')", name='ck_script_layer'),
        CheckConstraint("(layer='SPEECH' AND visibility='PUBLIC') OR (layer IN ('THOUGHT','NARRATION') AND visibility='OWNER')", name='ck_script_visibility'),
        CheckConstraint('weight > 0 AND is_active IN (0,1)', name='ck_script_weight_active'),
        Index('ix_script_candidate','situation_code','is_active','layer','version_id'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='스크립트 ID')
    code: Mapped[str] = mapped_column(String(100), unique=True, comment='스크립트 고유 코드')
    version_id: Mapped[int] = mapped_column(ForeignKey('script_pack_version.id'), comment='소속 묶음 버전 ID')
    situation_code: Mapped[str] = mapped_column(String(40), comment='상황 코드')
    action_code: Mapped[str | None] = mapped_column(String(40), nullable=True, comment='행동 코드, NULL이면 공통')
    layer: Mapped[str] = mapped_column(String(12), comment='발화·속마음·행동 서술 층')
    visibility: Mapped[str] = mapped_column(String(8), comment='PUBLIC공개 OWNER소유자전용')
    content: Mapped[str] = mapped_column(Text, comment='허용된 변수만 포함한 대사 본문')
    priority: Mapped[int] = mapped_column(Integer, default=0, server_default='0', comment='조건 일치 후보 중 우선순위')
    weight: Mapped[int] = mapped_column(Integer, default=100, server_default='100', comment='동일 우선순위 내 추첨 가중치')
    is_active: Mapped[int] = mapped_column(Integer, default=1, server_default='1', comment='사용 여부: 0비활성 1활성')


class GameScriptCondition(Base):
    __tablename__ = 'game_script_condition'
    __table_args__ = (CheckConstraint('condition_group > 0', name='ck_script_condition_group'),
        CheckConstraint('(hp_min_percent IS NULL OR hp_min_percent BETWEEN 0 AND 100) AND (hp_max_percent IS NULL OR hp_max_percent BETWEEN 0 AND 100) AND (hp_min_percent IS NULL OR hp_max_percent IS NULL OR hp_min_percent <= hp_max_percent)', name='ck_script_hp_range'),
        CheckConstraint('keyword_id IS NOT NULL OR map_id IS NOT NULL OR hp_min_percent IS NOT NULL OR hp_max_percent IS NOT NULL', name='ck_script_condition_nonempty'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='대사 적용 조건 ID')
    script_id: Mapped[int] = mapped_column(ForeignKey('game_script.id', ondelete='CASCADE'), index=True, comment='스크립트 ID')
    condition_group: Mapped[int] = mapped_column(Integer, default=1, server_default='1', comment='그룹 내부 AND, 그룹 사이 OR')
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey('personality_keyword.id'), nullable=True, comment='필수 성격 키워드 ID')
    map_id: Mapped[int | None] = mapped_column(ForeignKey('map.id'), nullable=True, comment='대상 맵 ID')
    hp_min_percent: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='최소 HP 비율')
    hp_max_percent: Mapped[int | None] = mapped_column(Integer, nullable=True, comment='최대 HP 비율')


class ScriptSubmission(Base):
    __tablename__ = 'script_submission'
    __table_args__ = (UniqueConstraint('version_id','applicant_id', name='uq_script_submission'),
        CheckConstraint("status IN ('PENDING','APPROVED','REJECTED')", name='ck_submission_status'),
        CheckConstraint('reward_amount >= 0 AND reward_paid IN (0,1)', name='ck_submission_reward'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='공통 등록 신청 ID')
    version_id: Mapped[int] = mapped_column(ForeignKey('script_pack_version.id'), comment='신청한 묶음 버전 ID')
    applicant_id: Mapped[int] = mapped_column(ForeignKey('users.id'), comment='신청 사용자 ID')
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey('users.id'), nullable=True, comment='심사 운영자 ID')
    status: Mapped[str] = mapped_column(String(12), default='PENDING', server_default='PENDING', comment='심사 상태')
    reward_amount: Mapped[int] = mapped_column(Integer, default=0, server_default='0', comment='예정된 무료 재화 보상')
    reward_paid: Mapped[int] = mapped_column(Integer, default=0, server_default='0', comment='보상 처리 여부, 지급 기능은 미구현')
    review_note: Mapped[str] = mapped_column(String(500), default='', server_default='', comment='심사 의견')


class UserScriptPack(Base):
    __tablename__ = 'user_script_pack'
    __table_args__ = (UniqueConstraint('user_id','version_id', name='uq_user_script_version'),)
    id: Mapped[int] = mapped_column(primary_key=True, comment='묶음 사용권 ID')
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), comment='사용권 보유 사용자 ID')
    version_id: Mapped[int] = mapped_column(ForeignKey('script_pack_version.id'), comment='사용 가능한 고정 버전 ID')
    source: Mapped[str] = mapped_column(String(20), comment='획득 경로: 작성·지급·향후 구매 등')


class CharacterScriptPack(Base):
    __tablename__ = 'character_script_pack'
    __table_args__ = (UniqueConstraint('character_id','version_id', name='uq_character_script_version'),
        CheckConstraint("mode IN ('PREFER','MIX')", name='ck_character_script_mode'))
    id: Mapped[int] = mapped_column(primary_key=True, comment='캐릭터 적용 묶음 ID')
    character_id: Mapped[int] = mapped_column(ForeignKey('character.id', ondelete='CASCADE'), comment='사용할 캐릭터 ID')
    version_id: Mapped[int] = mapped_column(ForeignKey('script_pack_version.id'), comment='적용한 고정 버전 ID')
    mode: Mapped[str] = mapped_column(String(8), default='PREFER', server_default='PREFER', comment='전용 우선 PREFER 또는 공통 혼합 MIX')
