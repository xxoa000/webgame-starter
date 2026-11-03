"""캐릭터 생성 규칙. 값 변경 후 필요하면 데이터 마이그레이션도 추가한다."""
CORE_STATS = ("strength", "stamina", "intelligence", "agility", "luck")
STAT_TOTAL = 20
STAT_RANGES = {key: (1, 16) for key in CORE_STATS}
MAX_REROLLS = 10

HP_PER_STAMINA = 10
MP_PER_INTELLIGENCE = 10
STAMINA_INTERVAL_SECONDS = 300
REST_MIN_PERCENT = 5
REST_MAX_PERCENT = 30
