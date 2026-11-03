# DB 컬럼 설명

모든 시각은 UTC 기준이다. MySQL 모델 정의를 기준으로 작성했다.

## character

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `user_id` | INTEGER | 아니오 | 사용자 ID |
| `name` | VARCHAR(24) | 아니오 | 이름 |
| `name_key` | VARCHAR(64) | 예 | 이름 중복 검사 키 |
| `gender` | VARCHAR(12) | 아니오 | 성별 |
| `age` | INTEGER | 예 | 나이(세) |
| `bio` | VARCHAR(500) | 아니오 | 프로필 소개 |
| `appearance` | JSON | 예 | 프로필 프리셋 정보 |
| `stats` | JSON | 아니오 | 능력치 정보 |
| `rerolls` | INTEGER | 아니오 | 남은 능력치 재추첨 횟수 |
| `hp_current` | INTEGER | 예 | 현재 HP |
| `mp_current` | INTEGER | 예 | 현재 MP |
| `stamina_current` | INTEGER | 예 | 현재 스태미나 |
| `stamina_updated_at` | DATETIME | 예 | 스태미나 회복 기준 시각(UTC) |
| `status` | VARCHAR(12) | 아니오 | 진행 상태 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## deleted_character

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `original_character_id` | INTEGER | 아니오 | 원래 캐릭터 ID |
| `user_id` | INTEGER | 아니오 | 사용자 ID |
| `name` | VARCHAR(24) | 아니오 | 이름 |
| `gender` | VARCHAR(12) | 아니오 | 성별 |
| `age` | INTEGER | 예 | 나이(세) |
| `bio` | VARCHAR(500) | 아니오 | 프로필 소개 |
| `appearance` | JSON | 예 | 프로필 프리셋 정보 |
| `stats` | JSON | 아니오 | 능력치 정보 |
| `rerolls` | INTEGER | 아니오 | 남은 능력치 재추첨 횟수 |
| `status` | VARCHAR(12) | 아니오 | 진행 상태 |
| `deleted_at` | DATETIME | 아니오 | 삭제 또는 사망 시각(UTC) |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## drop_item

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `item_id` | INTEGER | 아니오 | 아이템 ID |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## encyclopedia

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `character_id` | INTEGER | 아니오 | 캐릭터 ID |
| `item_id` | INTEGER | 아니오 | 아이템 ID |
| `first_map_id` | INTEGER | 예 | 최초 발견 맵 ID |
| `discovered_at` | DATETIME | 아니오 | 최초 발견 시각(UTC) |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## exploration

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `character_id` | INTEGER | 아니오 | 캐릭터 ID |
| `map_id` | INTEGER | 아니오 | 맵 ID |
| `status` | VARCHAR(16) | 아니오 | 진행 상태 |
| `turn` | INTEGER | 아니오 | 진행 턴 수 |
| `version` | INTEGER | 아니오 | 동시 요청 검증 번호 |
| `pending_item_id` | INTEGER | 예 | 회수 대기 아이템 ID |
| `pending_quantity` | INTEGER | 아니오 | 회수 대기 수량 |
| `combat` | JSON | 예 | 진행 중인 전투 상태 |
| `history` | JSON | 아니오 | 최근 탐색 기록 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## farming_item

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `item_id` | INTEGER | 아니오 | 아이템 ID |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## grimoire

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `magic_name` | VARCHAR(100) | 아니오 | 마법 이름 |
| `description` | TEXT | 아니오 | 설명 |
| `power` | INTEGER | 아니오 | 마법 위력 |
| `mana_cost` | INTEGER | 아니오 | 필요 MP |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## inventory

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `character_id` | INTEGER | 아니오 | 캐릭터 ID |
| `slot_capacity` | INTEGER | 아니오 | 최대 보관 종류 수 |
| `max_weight_grams` | INTEGER | 아니오 | 최대 수용 무게(g) |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## inventory_entry

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `inventory_id` | INTEGER | 아니오 | 인벤토리 ID |
| `item_id` | INTEGER | 아니오 | 아이템 ID |
| `quantity` | INTEGER | 아니오 | 보유 수량 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## item

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `name` | VARCHAR(100) | 아니오 | 이름 |
| `description` | TEXT | 아니오 | 설명 |
| `weight_grams` | INTEGER | 아니오 | 개당 무게(g) |
| `kind` | VARCHAR(20) | 아니오 | 아이템 분류 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## login_session

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `token_hash` | VARCHAR(64) | 아니오 | 세션 토큰 해시 |
| `user_id` | INTEGER | 아니오 | 사용자 ID |
| `expires_at` | DATETIME | 아니오 | 세션 만료 시각(UTC) |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## map

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `name` | VARCHAR(80) | 아니오 | 이름 |
| `description` | TEXT | 아니오 | 설명 |
| `empty_weight` | INTEGER | 아니오 | 빈손 결과 추첨 가중치 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## map_farming_item

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `map_id` | INTEGER | 아니오 | 맵 ID |
| `farming_item_id` | INTEGER | 아니오 | 파밍 아이템 ID |
| `weight` | INTEGER | 아니오 | 추첨 가중치 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## map_monster

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `map_id` | INTEGER | 아니오 | 맵 ID |
| `monster_id` | INTEGER | 아니오 | 몬스터 ID |
| `weight` | INTEGER | 아니오 | 추첨 가중치 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## monster

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `name` | VARCHAR(100) | 아니오 | 이름 |
| `description` | TEXT | 아니오 | 설명 |
| `hp` | INTEGER | 아니오 | 최대 HP |
| `attack_min` | INTEGER | 아니오 | 최소 공격력 |
| `attack_max` | INTEGER | 아니오 | 최대 공격력 |
| `defense` | INTEGER | 아니오 | 방어력 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## monster_drop_item

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `monster_id` | INTEGER | 아니오 | 몬스터 ID |
| `drop_item_id` | INTEGER | 아니오 | 전리품 아이템 ID |
| `weight` | INTEGER | 아니오 | 추첨 가중치 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## posts

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 게시글 ID |
| `title` | VARCHAR(200) | 아니오 | 게시글 제목 |
| `content` | TEXT | 아니오 | 게시글 본문 |
| `username` | VARCHAR(24) | 아니오 | 작성자 로그인 아이디 |
| `is_notice` | TINYINT | 아니오 | 공지 여부: 0일반 1공지 |
| `post_status` | TINYINT | 아니오 | 글 상태: 0숨김 1활성 2제재 3삭제 |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## recipe

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 고유 ID |
| `name` | VARCHAR(100) | 아니오 | 이름 |
| `main_item_id` | INTEGER | 아니오 | 주재료 아이템 ID |
| `sub_item1_id` | INTEGER | 예 | 첫 번째 부재료 ID |
| `sub_item2_id` | INTEGER | 예 | 두 번째 부재료 ID |
| `result_item_id` | INTEGER | 아니오 | 조합 결과 아이템 ID |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## users

| 컬럼 | MySQL 타입 | NULL 허용 | 설명 |
|---|---|---|---|
| `id` | INTEGER | 아니오 | 사용자 ID |
| `username` | VARCHAR(24) | 아니오 | 로그인 아이디 |
| `password_hash` | VARCHAR(255) | 아니오 | 비밀번호 해시 |
| `last_login_at` | DATETIME | 예 | 마지막 로그인 시각(UTC) |
| `user_status` | TINYINT | 아니오 | 계정 상태: 0휴면 1활성 2제재 3탈퇴 |
| `auth` | TINYINT | 아니오 | 권한: 0USER 1STAFF 9ADMIN |
| `create_at` | DATETIME | 아니오 | 생성 시각(UTC) |
| `update_at` | DATETIME | 아니오 | 마지막 수정 시각(UTC) |

## alembic_version

| 컬럼 | 타입 | 설명 |
|---|---|---|
| version_num | VARCHAR(32) | 적용된 마이그레이션 버전 |
| create_at | DATETIME | 생성 시각(UTC) |
| update_at | DATETIME | 마지막 수정 시각(UTC) |