# 기능별 백엔드 + Alembic

## 폴더 구조

```text
backend/
├── Dockerfile
├── requirements.txt
├── requirements.lock.txt
├── alembic.ini
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 0001_initial_tables.py
│       ├── 0002_character_age_stats.py
│       └── 0003_character_names_archive.py
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   └── security.py
│   ├── database/
│   │   ├── base.py
│   │   ├── session.py
│   │   ├── metadata.py
│   │   └── checks.py
│   └── modules/
│       ├── users/
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── router.py
│       │   ├── service.py
│       │   └── repository.py
│       ├── characters/
│       │   ├── models.py
│       │   ├── schemas.py
│       │   ├── router.py
│       │   ├── service.py
│       │   ├── repository.py
│       │   ├── rules.py
│       │   ├── stats.py
│       │   └── names.py
│       └── posts/
│           ├── models.py
│           ├── schemas.py
│           ├── router.py
│           ├── service.py
│           └── repository.py
└── tests/
    ├── test_flow.py
    └── test_alembic.py
```

각 파이썬 패키지에는 __init__.py도 있다.

## 파일별 책임

| 파일 | 역할 | 수정 예시 |
| --- | --- | --- |
| models.py | SQLAlchemy 테이블·관계 | 캐릭터 컬럼 추가 |
| schemas.py | API 입력 검증·응답 형식 | 이름 길이·나이 범위 |
| router.py | HTTP 경로·인증 의존성·호출 연결 | API 경로 추가 |
| service.py | 기능 규칙·트랜잭션·커밋 | 재추첨 허용 조건·삭제 조건 |
| repository.py | DB 조회·이름 중복 검사·행 잠금 | 검색 조건 변경 |

users는 회원가입·로그인·세션 기능을 포함한다. URL은 기존 /auth/...를 유지하므로 프론트를 바꿀 필요가 없다. 현재 내 계정과 캐릭터를 함께 반환하는 /me는 characters/router.py에 있다.

characters/models.py에 활성 캐릭터와 삭제 이력 모델이 함께 있다. 같은 기능의 모델이므로 서로 다른 상위 폴더로 흩뜨리지 않았다. 삭제 이력의 user_id는 UNIQUE가 아니며 회원 1명에 여러 이력이 연결된다.

posts는 파일 구조만 마련했다. 게시글 기능·테이블·API는 아직 구현하거나 등록하지 않았다. 게시글 필드와 권한이 정해지면 이곳에 추가하고 database/metadata.py에 모델 import, main.py에 라우터 등록을 추가한다.

| 공통 파일 | 역할 |
| --- | --- |
| app/main.py | 앱 조립·CORS·출처 검사 로그·라우터 등록 |
| app/core/config.py | DATABASE_URL·프론트 주소·쿠키·세션 설정 |
| app/core/security.py | 로그인 사용자·비밀번호 해시·세션 해시 |
| app/database/base.py | 전체 모델의 공통 Base |
| app/database/session.py | 엔진과 요청별 세션 |
| app/database/metadata.py | Alembic autogenerate용 전체 모델 등록 |
| app/database/checks.py | 서버 시작 전 revision 확인 |
| app/modules/characters/rules.py | 스탯 범위·합계·재추첨 횟수 |
| app/modules/characters/stats.py | 합계 20의 랜덤 분배 |
| app/modules/characters/names.py | 이름 정규화·중복 키 |
| alembic/versions/ | 실제 DB 변경 이력 |

## Alembic 전환

앱 시작 시 create_all을 실행하지 않는다. DB 생성과 변경은 alembic upgrade head로 수행한다. 적용 상태는 alembic_version 테이블에서 관리한다. DB 연결 주소는 Docker가 주입한 DATABASE_URL을 앱과 Alembic이 공유하며 ini에 비밀번호를 넣지 않는다.

- 0001: 초기 테이블 생성 또는 기존 기본 테이블 구조 확인.
- 0002: age 컬럼 추가 및 합계 20에 맞지 않는 기존 기본 스탯만 재분배.
- 0003: 활성 이름 중복 방지 및 삭제 이력 테이블 생성.

새 DB, 수동 v2 전 DB, v2 적용 DB, v3 적용 DB 모두 upgrade head 한 번으로 편입한다. 유효한 기존 스탯·나이·회원·비밀번호 해시·세션·삭제 이력은 유지한다. 기존 이름 중복이 있으면 ID를 출력하고 중단한다. 이름을 정리한 뒤 같은 명령을 재실행한다. 테이블 이름은 client/login_session/character/deleted_character 그대로 유지한다.

기존 합계 20 규칙에 맞지 않는 캐릭터의 기본 스탯 5개는 0002에서 재추첨된다. 외모·키·프로필·재추첨 사용 횟수는 유지한다. 실행 전 DB를 백업하고 변경 요청을 보내는 백엔드를 정지한다.

이미 수동 v2·v3를 적용했더라도 alembic stamp head로 건너뛰지 않는다. 실제 스키마를 확인하며 upgrade head를 실행한다. 알 수 없는 다른 Alembic revision이 들어 있는 DB는 자동으로 덮어쓰지 않는다.

초기 편입 revision 3개는 데이터 보존을 위해 자동 downgrade를 차단한다. 특히 이전 스탯 재분배는 역산할 수 없다. 이후 새 revision은 변경 내용에 맞는 upgrade/downgrade를 작성한다. MySQL DDL은 암묵적 커밋이 있으므로 전체 변경이 한 트랜잭션으로 롤백되지는 않는다.

## 프로젝트 최상위에서 사용하는 명령

```bash
docker compose run --rm --no-deps backend alembic upgrade head
docker compose run --rm --no-deps backend alembic current
docker compose run --rm --no-deps backend alembic history
```

## 다음 컬럼 변경을 추가할 때

모델을 수정하고 백엔드를 빌드한 뒤, revision 파일이 컨테이너 종료와 함께 사라지지 않도록 alembic 폴더를 연결한다.

프로젝트 최상위에서:

```bash
docker compose build backend
docker compose run --rm --no-deps \
  -v "$PWD/backend/alembic:/app/alembic" \
  backend alembic revision --autogenerate -m "add character field"
```

생성된 backend/alembic/versions 파일을 검토한다. 자동 생성 결과를 그대로 믿지 말고 데이터 이전·제약·되돌리기를 확인한다. 그다음 새 revision을 이미지에 포함하고 적용한다.

```bash
docker compose stop backend frontend
docker compose build backend
docker compose run --rm --no-deps backend alembic upgrade head
python3 scripts/start.py
```

Python을 맥 전역에 설치할 필요는 없다. 위 명령은 컨테이너 안에서 실행된다. .venv 개발 시에는 backend 폴더에서 의존성을 설치하고 DATABASE_URL을 올바르게 설정한 다음 python -m alembic 명령을 사용할 수 있다.

## 테스트

backend 폴더의 파이썬 환경에서 python -m pytest -q를 실행한다. 테스트는 임시 SQLite DB를 사용하므로 실제 MySQL 동시성·DDL 검증을 대신하지 않는다.

참고: https://alembic.sqlalchemy.org/en/latest/tutorial.html
