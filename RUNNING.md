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

DB 초기화 완료 후 마이그레이션하고 앱을 시작하는 순서다. 최신 DB 리비전은 `0016_jwt_auth`이다. 이미 적용된 변경은 Alembic이 건너뛴다. 새 DB에도 과거 이력부터 최신까지 순서대로 적용한다.

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

## 스크립트 표시 업데이트 적용

이번 압축파일은 변경 파일만 포함한다. 프로젝트 최상위에서 병합하여 적용한다. .env는 포함하지 않는다.

업로드된 0012 마이그레이션은 grimoire를 삭제하고 skill을 새로 생성한다. 이 파일은 이번 패치에서 수정하지 않았다. 아직 0012를 적용하지 않았다면 기존 데이터가 필요한지 확인하고, 삭제/생성 대신 테이블 및 magic_name 컬럼 이름 변경으로 고친 뒤 진행해야 한다. 이미 삭제된 데이터는 이번 패치로 복원되지 않는다.

0012가 정상 적용된 DB에서는 다음 명령을 실행한다.

```bash
docker compose stop backend
docker compose build backend frontend
docker compose run --rm --no-deps backend alembic current
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend frontend
```

최종 revision은 `0013_script_display`다. 0013은 대사 본문과 조건을 보존하고 visibility 컬럼과 관련 CHECK를 제거한 뒤 조회 VIEW를 추가한다. 기존 탐색 기록 JSON은 그대로 두되 응답에서 과거 visibility 필드를 제외한다.

```sql
SELECT * FROM game_script_keyword_view
ORDER BY situation_code, script_id, condition_group, condition_id;
```

검증: 스크립트 선택·확률 경계·편집 뷰·0013 업/다운 시 원문 보존·탐색/전투 관련 17개 테스트 통과. 기존 테스트 2개는 이전 grimoire 이름을 기대하거나 업로드된 0012의 MySQL 전용 DDL을 SQLite에서 실행하여 실패했다. 해당 기존 테스트/0012는 이번 패치에 포함하지 않는다. 실제 MySQL 적용과 브라우저 시각 검증은 수행하지 않았다.

## 평면 지도 관측 화면 적용

`script-console-update.zip`의 0013이 적용된 프로젝트 기준 변경 파일이다. 프로젝트 최상위에서 병합한 뒤 다음 명령을 실행한다. .env·포트·Compose 설정은 수정하지 않는다.

```bash
unzip -o "$HOME/Downloads/drone-exploration-update.zip" -d .
docker compose stop backend
docker compose build backend frontend
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend frontend
```

최종 revision: `0014_drone_observation`. 새 `exploration_presence` 테이블과 `exploration.position_step`을 추가한다. 기존 대사·키워드·맵 데이터는 갱신하지 않는다. 예전 맵 탐색 세션의 위치는 첫 지점에서 시작하며 기존 턴은 유지한다.

지도 좌표와 이동 경로는 `frontend/lib/droneMap.ts`, 지형 그리기는 `frontend/components/exploration/DroneMap.tsx`, 높이·색감은 `frontend/styles/bureau/drone-observation.css`에서 수정한다. 지도는 임의로 설계한 게임용 평면 지형이며 GPS나 충돌 판정 기능은 아니다.

온라인 인원은 탐색 페이지가 보이는 동안 25초마다 서버에 접속 신호를 전송하고, 같은 맵의 진행 중인 캐릭터 중 최근 90초 이내 신호가 있는 계정만 집계한다. 숨긴 탭과 페이지를 떠난 사용자는 최대 90초 후 제외된다. 종료·사망·제재 상태는 집계에서 제외한다. 여러 탭을 열어도 계정당 한 명으로 계산한다. 집계 요청에 실패하면 0명 대신 —를 표시한다.

브라우저 수동 확인: 전체 지도에서 구역 선택 → 원격 탐색 개시 → 상세 지도/초록 점/해당 맵 인원 확인 → 탐색 시 이동, 휴식 시 제자리 확인 → 새로고침 후 위치 유지 → 탐색 종료 후 전체 지도 복귀.

검증: 관련 백엔드 테스트 21개 통과(기존 0012·grimoire 관련 테스트 2개 제외), 프론트 타입 검사 및 프로덕션 빌드 통과. 로컬 브라우저는 실행 환경 제약으로 실행하지 못했으며 실제 MySQL 마이그레이션은 미검증이다.

## CSV로 초기 공통 대사 덮어쓰기

`script-seed-db-update.zip`을 프로젝트 최상위에 병합한다. 0013 이상 스키마가 적용되어 있어야 한다. 새 마이그레이션은 추가하지 않는다. CSV만 교체하면 DB는 바뀌지 않으므로 아래 명령을 실행한다.

```bash
unzip -o "$HOME/Downloads/script-seed-db-update.zip" -d .
docker compose stop backend
docker compose build backend
docker compose run --rm --no-deps \
  -v "$PWD/SCRIPTS-SEED.csv:/seed/SCRIPTS-SEED.csv:ro" \
  -v "$PWD/SCRIPT-CONDITIONS-SEED.csv:/seed/SCRIPT-CONDITIONS-SEED.csv:ro" \
  backend python -m app.modules.scripts.import_seed
docker compose up -d --no-deps backend
```

덮어쓰기 범위는 `initial_common`(기존 `INITIAL_COMMON`) 공통 묶음의 1판이다. CSV의 본문·코드·우선순위·가중치·활성 여부·조건으로 기존 데이터를 교체한다. 해당 판에만 존재하던 잉여 대사는 제거한다. 다른 개인/판매 원고와 다른 판은 보존한다. 기존 키워드 ID와 캐릭터의 성격 선택은 보존하고 참조하는 키워드의 code를 소문자로 통일한다.

같은 코드 또는 상황·층·조건에 해당하는 기존 대사의 ID를 우선 재사용한다. 기존 178개 초기 데이터라면 178개 갱신 + 155개 추가로 333개가 된다. 반복 실행해도 중복 추가되지 않는다. 이미 출력된 탐색 기록 JSON의 본문은 변경하지 않고 새 이벤트부터 수정 내용을 사용한다. 전체 교체는 하나의 트랜잭션이며 오류 시 모두 되돌린다.

`keyword_name`은 편집용 표시 컬럼으로 DB에 중복 저장하지 않는다. 조건 파일의 이름은 실제 DB 이름과 검증하며 연결은 keyword_code로 한다. `code`·`script_code`·`keyword_code`는 영문 소문자이고 `layer`는 기존 DB 규칙인 SPEECH/THOUGHT/NARRATION을 유지한다.

```sql
SELECT COUNT(*) AS script_count
FROM game_script s
JOIN script_pack_version v ON v.id=s.version_id
JOIN script_pack p ON p.id=v.pack_id
WHERE p.code='initial_common' AND v.version=1;

SELECT script_id, code, situation_code, keyword_name, content
FROM game_script_keyword_view
ORDER BY situation_code, script_id, condition_group;
```

검증: SQLite에서 기존 ID 보존·다른 묶음 보존·교체 후 재실행·실패 롤백·코드 충돌 거부를 테스트했다. 사용자 Mac의 실제 MySQL DB는 여기서 직접 변경하지 않았다.

## 빈사·구조·인벤토리·상점 업데이트

이 패치에는 대사 CSV와 대사 시드/불러오기 모듈을 포함하지 않는다. 현재 편집 중인 원문은 그대로 보존한다. 프로젝트 최상위에서 병합한 뒤 적용한다. .env와 Compose 설정 변경은 없다.

```bash
unzip -o "$HOME/Downloads/rescue-shop-update.zip" -d .
docker compose stop backend
docker compose build backend frontend
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend frontend
```

최종 revision은 `0015_rescue_shop`. character.downed, users.money, item.buy_price/sell_price, rescue_request 테이블을 추가한다. 기존 계정에 초기 무료 크레딧 1,000을 부여한다. 상점 상품 가격은 새 마이그레이션에서 5개 회복 물자에만 지정한다. 과거 맵·대사 데이터는 수정하지 않는다.

치료 NPC 도착 시간은 backend/app/modules/rescue/service.py의 NPC_RESCUE_SECONDS=60에서 조절한다. 구조 요청 후 서버 기한은 DB에 저장되어 재접속해도 유지된다. 별도 작업 큐 없이 대상이 탐색 상태를 다시 조회할 때 도착을 확정한다.

신규 경로: GET /shop, POST /shop/buy, POST /shop/sell, POST /inventory/use, POST /inventory/discard, POST /rescue/request, POST /rescue/abandon, GET /rescue/nearby, POST /rescue/{id}/help. 거래·버리기는 양수 정수 수량만 허용한다.

검증 범위는 자동 API 테스트·SQLite 마이그레이션 보존·프론트 타입 검사·빌드다. 실제 MySQL 적용과 브라우저 화면 조작은 별도 확인이 필요하다.

이번 업데이트 검증: 관련 API·상태·거래·구조·회귀 테스트 63개 통과. 업로드된 과거 0012의 SQLite 비호환 DDL을 거치는 테스트 2개와 이전 grimoire 테이블명을 기대하는 테스트 1개는 제외했다. 0015는 별도로 기존 데이터 보존 및 되돌리기를 검증했다. 브라우저 검증 환경에서 로컬 서버 연결이 거부되어 실제 화면 조작 검증은 수행하지 못했다.


## JWT 인증 전환 (0016)

기존 업데이트(0015)까지 적용한 프로젝트에 변경 파일을 병합한다. `.env`, 포트 선택 스크립트와 대사 CSV는 제공 ZIP에 포함하지 않는다. compose.yaml은 backend.environment에 JWT_SECRET_KEY와 JWT_ACCESS_HOURS를 전달하는 두 줄만 추가했다. 로컬에서 Compose를 별도로 수정했다면 해당 두 줄만 병합한다.

서명키는 운영자가 한 번 생성하고 안전하게 보관한다. 아래 명령은 키를 출력할 뿐 파일을 수정하지 않는다.

```bash
openssl rand -hex 32
```

출력한 값을 프로젝트 최상위 `.env`에 **직접** 추가한다. 기존 DB 비밀번호나 포트는 유지한다.

```dotenv
JWT_SECRET_KEY=위에서_생성한_값
JWT_ACCESS_HOURS=24
```

JWT_SECRET_KEY는 백엔드만 사용한다. 프론트 환경변수나 NEXT_PUBLIC_ 접두사로 전달하지 않는다. 무작위 32바이트 이상 키가 없으면 서버는 시작하지 않는다. 여러 백엔드 인스턴스는 동일한 키를 사용해야 하며, 키를 변경하면 기존 JWT가 모두 무효화된다. 기존 SESSION_HOURS 설정은 사용하지 않고 JWT_ACCESS_HOURS를 사용한다.

```bash
docker compose stop backend
docker compose build backend
docker compose run --rm --no-deps backend alembic upgrade head
docker compose up -d --no-deps backend
docker compose logs -f backend
```

최신 head는 `0016_jwt_auth`다. 이 마이그레이션은 users.token_version을 추가하고 login_session 테이블을 제거한다. 기존 로그인은 해제되므로 다시 로그인한다. 계정·권한·비밀번호·게임 데이터와 대사 데이터는 유지한다. downgrade는 빈 세션 테이블만 복구하며 폐기한 세션은 되살리지 않는다.

프론트는 기존 credentials: include 쿠키 전송을 그대로 사용하므로 수정·재빌드가 필요 없다. 운영 HTTPS에서는 기존 COOKIE_SECURE를 true로 설정한다. JWT는 암호화된 데이터가 아니며 사용자 ID와 토큰 검증용 정보만 넣는다. 권한은 매 요청 DB에서 읽으며 JWT 안의 auth 값을 신뢰하지 않는다. 로그아웃은 계정의 기존 모든 JWT를 무효화한다. 만료 후 재로그인하며 refresh 토큰은 이번 범위에 포함하지 않는다.

검증 기준: PyJWT 공식 API의 고정 알고리즘 및 필수 클레임 검증 사용.
https://pyjwt.readthedocs.io/en/stable/api.html

이번 JWT 업데이트는 인증·권한·로그아웃·마이그레이션 및 기존 게임 회귀 테스트 79개를 통과했다. 기존 0012 SQLite 비호환 DDL 관련 2개와 과거 grimoire 이름을 기대하는 1개는 제외했다. 0016 적용·되돌리기는 격리된 SQLite DB에서 검증했다. 실제 MySQL 업그레이드와 브라우저 조작 검증은 수행하지 않았다.
## 공유 균열 레이드 적용 (0018)

최신 마이그레이션은 `0018_shared_raids`다. 백엔드를 정지한 상태에서 기존 실행 방식에 맞춰 의존성과 이미지를 갱신하고 `alembic upgrade head`를 실행한 뒤 서버를 재시작한다. 호스트 가상환경에서는 backend 폴더에서 `.venv/bin/python -m alembic upgrade head`를 실행한다. Compose 방식에서는 프로젝트 최상위에서 `docker compose run --rm --no-deps backend alembic upgrade head`를 실행한다. 실행 전 기존 DATABASE_URL과 JWT 서명키를 유지한다.

`raid_cycle`, `raid_event`, `raid_member` 테이블과 `exploration.pending_raid_id`를 추가한다. 기존 캐릭터·아이템·탐색 기록은 유지한다. 보상 기록 보존을 위해 자동 downgrade는 제공하지 않는다. 별도의 Redis나 작업 큐는 필요하지 않다.

서버 시작 후 `/health`와 Alembic head를 확인한다. `GET /raids/current`는 공개 이벤트, `GET /raids/mine`은 로그인한 사용자의 결정·보상 현황을 반환한다. 보스 공격은 `POST /raids/{event_id}/attack`에 최신 `version`을 전달한다. 수치·보상 규칙과 조절 가능한 환경변수는 RULE.md의 공유 균열 항목을 따른다. 새 기본값은 다음 이벤트부터 수집 목표·보스 HP에 적용된다.

검증은 backend의 `python -m pytest -q`, frontend의 `npm run typecheck`, `npm run check:styles`, `npm run build`로 수행한다. UI에서는 홈 경보 → 붉은 이벤트 맵 → 결정 회수 → 보스 출현 → 다른 탐사자와 공유 HP 갱신 → 종료 및 캐릭터 미분배 포인트를 확인한다.
