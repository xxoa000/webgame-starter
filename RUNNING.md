# RUNNING — 실행·업데이트·문제 확인

모든 Docker Compose 명령은 compose.yaml이 있는 프로젝트 최상위에서 실행한다. 의존성·인터프리터 설명은 [SETUP.md](SETUP.md)에 있다.

## 최초 실행

기존 .env의 DB 비밀번호와 포트 설정을 유지한다. 처음 받은 프로젝트에 .env가 없을 때만 예제 파일을 바탕으로 직접 준비한다.

```sh
docker compose build backend frontend
docker compose up -d --wait mysql
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend frontend
```

DB 초기화 완료 후 마이그레이션하고 앱을 시작하는 순서다. 최신 DB 리비전은 `0011_personality_scripts`다. 이미 적용된 변경은 Alembic이 건너뛴다. 새 DB에도 과거 이력부터 최신까지 순서대로 적용한다.

## 코드 업데이트

폴더 전체를 삭제·대치하지 않고 변경 파일을 병합하거나 Git으로 갱신한다. 특히 .env와 로컬 파일을 유지한다.

```sh
docker compose stop backend
docker compose build backend frontend
docker compose up -d --wait mysql
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend frontend
```

DB 변경이 없는 프론트 수정만 반영할 때:

```sh
docker compose up -d --no-deps --build frontend
```

백엔드 코드만 바꾸고 DB 구조가 그대로인 경우:

```sh
docker compose up -d --no-deps --build backend
```

Dockerfile은 소스를 복사하므로 호스트 파일 수정만으로 실행 이미지가 갱신되지 않는다. NEXT_PUBLIC_API_URL 변경도 프론트 재빌드가 필요하다. 이미 적용한 시드 파일을 편집한 것만으로 DB 원문이 바뀌지는 않는다.

## 정지·재시작

```sh
docker compose stop
docker compose start
```

위 명령은 이미 만들어진 컨테이너를 중지·재개한다. 새 빌드·새 환경 설정은 `up -d` 절차로 반영한다.

```sh
docker compose down
```

기본 down은 DB 이름 있는 볼륨을 유지한다. `down -v`는 DB 볼륨까지 제거하므로 정상적인 업데이트·마이그레이션 복구 명령으로 사용하지 않는다.

## 주소와 포트 확인

```sh
docker compose ps
docker compose port frontend 5174
docker compose port backend 8000
docker compose port mysql 3306
```

| 대상 | 컨테이너 내부 포트 | 호스트 주소 확인 |
|---|---:|---|
| 프론트 | 5174 | 출력된 공개 포트로 브라우저 접속 |
| 백엔드 | 8000 | 출력된 공개 포트의 /docs, /health |
| MySQL | 3306 | 출력된 공개 포트로 DBeaver 접속 |

`127.0.0.1:8002 → 8000`이면 브라우저 API 문서는 http://localhost:8002/docs다. 내부 포트는 다른 프로젝트와 같아도 되지만 동일한 호스트 IP·포트는 동시에 바인딩할 수 없다.

현재 제공된 compose.yaml은 백엔드 호스트 8000, 프론트 호스트 5174가 고정이며 MySQL은 MYSQL_PORT를 참조한다. 사용자가 이미 포트를 환경변수화한 파일은 그 정의를 따른다. 실제 실행 값은 위 명령이 기준이다. .env의 BACKEND_PORT·FRONTEND_PORT가 고정 매핑을 자동 변경하지는 않는다.

`scripts/start.py`는 선택한 포트를 현재 실행 환경으로 전달하고 .env를 저장하지 않는다. 그러나 Compose 매핑이 그 변수를 참조하지 않으면 선택값이 적용되지 않는다. 따라서 기본 실행 안내는 위의 명시적 Compose 절차를 사용하며, 모든 포트 충돌이 자동 해결된다고 가정하지 않는다.

## 프론트·백엔드 주소 일치

| 항목 | 맞춰야 할 값 |
|---|---|
| NEXT_PUBLIC_API_URL | 브라우저에서 접근 가능한 백엔드의 호스트 주소 |
| FRONTEND_ORIGIN | 실제 프론트 주소의 프로토콜·호스트·포트 |
| DATABASE_URL의 호스트 | Docker 백엔드에서는 mysql:3306, 호스트 직접 실행에서는 127.0.0.1:공개포트 |

예를 들어 프론트가 http://localhost:5175, API가 http://localhost:8002라면 각 설정도 그 주소와 맞아야 한다. localhost와 127.0.0.1을 섞으면 출처·쿠키가 달라질 수 있으므로 브라우저 주소를 일관되게 사용한다.

## 관리자·스탭 지정

먼저 화면에서 일반 회원가입을 한다. 실제 로그인 아이디를 지정한다.

```sh
docker compose exec backend python -m app.modules.users.manage --username YOUR_LOGIN_ID --auth 9
```

| auth | 권한 |
|---:|---|
| 9 | ADMIN |
| 1 | STAFF |
| 0 | USER |

위 명령은 해당 계정의 권한만 바꾸고 .env·비밀번호를 수정하지 않는다. 권한 변경 후 화면을 새로고침하거나 다시 로그인한다. 공지는 게시판에서 운영 계정으로 작성하고 공지사항을 체크한다. 예전 하드코딩 공지는 자동 등록하지 않아 초기 공지 목록은 비어 있을 수 있다.

## DB 상태·로그

```sh
docker compose logs --tail=200 -f backend
docker compose logs --tail=100 -f frontend
docker compose logs --tail=100 -f mysql
docker compose exec backend alembic current
docker compose exec backend alembic heads
```

백엔드가 시작하지 못하면 `exec` 대신 새 임시 컨테이너로 확인한다.

```sh
docker compose run --rm --no-deps backend alembic current
docker compose run --rm --no-deps backend alembic heads
```

### DBeaver

Host는 localhost, Port는 `docker compose port mysql 3306`의 공개 포트, DB명은 webgame, 사용자명은 webgame이다. 비밀번호는 기존 설정의 애플리케이션 DB 비밀번호를 사용한다. MySQL URL을 웹 브라우저로 여는 방식은 아니다.

스키마를 새로고침하면 users 및 컬럼 COMMENT를 볼 수 있다. 직접 쓰는 SQL도 UTC 기준으로 맞추려면 해당 연결 세션에서 실행한다.

```sql
SET time_zone = '+00:00';
```

### 스크립트 원문 확인·수정

```sql
SELECT id, code, situation_code, layer, priority, weight, content
FROM game_script
ORDER BY situation_code, layer, priority DESC, id;

UPDATE game_script
SET content = '참, 빈손으로 돌아가게 생겼군.'
WHERE code = 'empty_K3_1';
```

개발 중 원문을 바꾸면 이후 사건부터 사용한다. 이미 기록한 출력은 당시 문장 스냅샷으로 유지된다. 고유 code를 기준으로 구분하고, 기존 숫자 ID가 예시와 같다고 가정하지 않는다. 새 시드는 새 code와 전진 마이그레이션으로 관리한다.

## 개발 서버 직접 실행 — 선택 사항

### 백엔드

[SETUP.md](SETUP.md)의 backend/.venv를 활성화한다. backend 폴더에서 실행하며, 호스트에서 접속 가능한 MySQL 공개 주소를 DATABASE_URL 환경변수로 설정해야 한다. Compose의 mysql:3306 주소를 그대로 복사하면 호스트에서 연결되지 않는다.

```sh
alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

포트 충돌 시 사용할 포트를 직접 지정하고 프론트 API 주소와 출처를 함께 맞춘다. DATABASE_URL을 생략하면 설정상 SQLite 기본 주소가 사용되므로 의도치 않은 별도 DB를 만들지 않도록 확인한다.

### 프론트

별도 터미널의 frontend 폴더에서 실행한다.

```sh
npm ci
npm run dev
```

직접 실행과 Compose 실행을 같은 호스트 포트에서 동시에 시작하지 않는다.

## 테스트와 검증 범위

백엔드 Dockerfile은 tests 폴더를 이미지에 복사하지 않는다. 프로젝트 최상위에서 테스트·실행 보조 소스만 읽기 전용으로 마운트한다. 환경변수 오버라이드는 이 테스트 컨테이너에만 적용되며 .env를 수정하지 않는다.

```sh
docker compose run --rm --no-deps \
  -e DATABASE_URL=sqlite:// \
  -e FRONTEND_ORIGIN=http://localhost:5174 \
  -v "$PWD/backend/tests:/app/tests:ro" \
  -v "$PWD/scripts:/scripts:ro" \
  backend python -m pytest -q tests

docker compose exec frontend npm run typecheck
```

로컬 .venv가 있다면 backend에서 `python -m pytest -q`를 실행한다. 프론트는 frontend에서 `npm run typecheck`, `npm run build`로 검사한다. 테스트는 격리된 SQLite를 사용하며 실제 서비스 DB 초기화 명령이 아니다. MySQL 행 잠금·실제 서버 연결은 별도 통합 검증 대상이다.

최근 코드 작업의 검증 기록은 백엔드 67개 통과, 프론트 타입 검사·프로덕션 빌드 통과다. 실제 MySQL 서버와 브라우저 조작 QA는 수행하지 않았다. 이번 문서 통합에서는 애플리케이션 테스트를 재실행하지 않고 문서 링크·경로·소스 보존을 확인한다.

## 자주 확인할 문제

| 현상 | 확인 순서 |
|---|---|
| Failed to fetch | backend 실행·공개 포트 → NEXT_PUBLIC_API_URL → Origin/CORS → 프론트 재빌드 |
| 허용되지 않은 출처 403 | 실제 프론트 주소와 FRONTEND_ORIGIN, 요청 Origin 확인 |
| 관리자 동작 403 | auth=9 여부, 재로그인·새로고침, 계정 상태 확인 |
| /me 등에서 500 | 백엔드 traceback과 alembic current/heads 확인 |
| 미적용 마이그레이션 | 올바른 backend 이미지로 upgrade head 후 재기동 |
| 이미 존재하는 테이블·DDL 실패 | 실패 리비전·DB 구조·로그 확인. 임의 stamp나 테이블 삭제로 넘기지 않음 |
| 기존 캐릭터가 탐색 불가 | 캐릭터 메뉴에서 최초 성격 세 분류 선택 |
| 호스트 포트 점유 | compose ps / port와 다른 프로젝트 컨테이너 확인 |
| 수정해도 화면·API가 같음 | 이미지 재빌드와 사용 중인 컨테이너 확인 |

## 과거 문서 정리

문서 ZIP은 네 문서만 포함한다. 압축 해제만으로 예전 문서가 삭제되지는 않으므로, 프로젝트 최상위에서 아래 명령으로 최상위의 다른 .md만 정리할 수 있다.

```sh
python3 - <<'PY'
from pathlib import Path
if not Path("compose.yaml").is_file():
    raise SystemExit("compose.yaml이 있는 프로젝트 최상위에서 실행해.")
keep = {"README.md", "SETUP.md", "RUNNING.md", "RULE.md"}
for path in Path(".").glob("*.md"):
    if path.is_file() and path.name not in keep:
        path.unlink()
PY
```

하위 폴더와 의존성·Git 파일·소스·.env는 대상이 아니다. 이전 패치 ZIP을 다시 풀면 옛 안내 파일이 재생성될 수 있으므로, 문서 기준은 이 네 파일로 유지한다.
