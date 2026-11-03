# SETUP — 의존성·라이브러리·버전 관리

실행 절차는 [RUNNING.md](RUNNING.md), 프로젝트 구조는 [README.md](README.md)를 참고한다.

## 권장 환경

| 항목 | 프로젝트 기준 |
|---|---|
| Docker Desktop / Compose | 기본 실행 도구 |
| Python | 백엔드 Docker 이미지 3.12-slim |
| Node.js | 프론트 Docker 이미지 24-alpine |
| MySQL | mysql:8.4 |
| 에디터 | VS Code 등. 로컬 분석 시 해당 프로젝트 인터프리터·TypeScript 사용 |

Docker로만 실행하면 Python·Node 라이브러리는 컨테이너 이미지에 설치된다. 맥 전역 Python에 프로젝트 라이브러리를 설치할 필요가 없다. VS Code의 로컬 타입 분석이나 호스트 직접 실행을 원할 때만 별도 .venv와 frontend/node_modules를 준비한다.

## 현재 잠금 버전

아래는 현재 저장소의 잠금 파일 기준이다. 전체 목록은 잠금 파일이 기준이며, 이 표를 설치 입력으로 사용하지 않는다.

| 영역 | 주요 고정 버전 |
|---|---|
| 프론트 | Next.js 16.4.3, React/React DOM 19.3.1, TypeScript 5.9.3 |
| 백엔드 | FastAPI 0.162.0, SQLAlchemy 2.1.6, Alembic 1.20.1 |
| 검증·서버 | pytest 9.2.0, Uvicorn 0.54.0, Pydantic 2.14.2 |

Dockerfile의 Python·Node·MySQL 태그는 메이저/마이너 태그이므로 이미지 자체의 모든 바이트까지 고정한 구성은 아니다. 릴리스 재현성이 필요하면 이미지 digest 고정도 별도로 관리한다.

## 환경 파일

기존 .env가 있으면 그대로 사용한다. 최초 복제이며 .env가 없을 때만 .env.example을 복사하고 직접 값을 설정한다. 기존 파일 위로 복사하지 않는다.

| 설정 | 용도 |
|---|---|
| MYSQL_PASSWORD | 애플리케이션 DB 계정 비밀번호 |
| MYSQL_ROOT_PASSWORD | MySQL 관리용 root 비밀번호 |
| MYSQL_PORT | 호스트에서 MySQL에 접속할 때의 공개 포트 |
| NEXT_PUBLIC_API_URL | 브라우저가 호출할 백엔드 주소. 프론트 빌드 시 반영 |
| FRONTEND_ORIGIN | 허용할 프론트 출처. 프로토콜·호스트·포트가 일치해야 함 |
| COOKIE_SECURE | 로컬 HTTP는 false, HTTPS 구성에서는 true |
| DATABASE_URL | 백엔드 DB 연결 문자열. Compose에서는 서비스 환경으로 전달 |

BACKEND_PORT·FRONTEND_PORT는 compose.yaml의 ports가 해당 변수를 참조하는 경우에만 적용된다. .env에 키를 추가하는 것만으로 고정된 포트 매핑이 바뀌지 않는다.

현재 Compose는 사용자명 webgame, DB명 webgame을 사용한다. 일반 DB 계정과 root는 별도다. 비밀번호를 URL에 직접 조립하는 구성에서는 예약 문자의 URL 인코딩이 필요하다. 영숫자 기반의 임의 문자열이 필요하면 아래 명령으로 생성할 수 있다.

```sh
openssl rand -hex 32
```

이미 초기화한 MySQL 볼륨의 계정 비밀번호는 .env 값만 바꾼다고 DB 내부에서 자동 변경되지 않는다. 기존 DB 자격 증명과 설정을 맞춘다. .env·실제 비밀번호·토큰은 Git에 올리지 않는다. NEXT_PUBLIC_ 변수는 브라우저에 노출되므로 비밀값을 넣지 않는다.

## Docker 의존성 설치

프로젝트 최상위에서 실행한다.

```sh
docker compose build backend frontend
```

백엔드 Dockerfile은 requirements.lock.txt로 pip 설치하고, 프론트 Dockerfile은 package-lock.json과 npm ci를 사용한다. 실행 중인 컨테이너 안에 수동으로만 설치한 라이브러리는 다음 빌드에 유지되지 않는다. 영구 변경은 의존성 파일과 새 이미지에 반영한다.

## 로컬 Python .venv — 선택 사항

아래는 Python 3.12 인터프리터가 설치된 경우다. 설치되어 있지 않으면 우선 Docker 실행을 사용한다.

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -c "import sys; print(sys.executable)"
```

출력 경로가 backend/.venv/bin/python인지 확인한다. VS Code의 Python: Select Interpreter에서도 같은 인터프리터를 선택한다. 작업 후 `deactivate`로 해제한다.

### Python 라이브러리 변경

직접 사용하는 라이브러리는 requirements.txt에서 버전 범위를 관리한다. 필요한 패키지를 깨끗한 프로젝트 .venv에서 설치하고 테스트한 뒤, 그 환경을 requirements.lock.txt에 고정한다.

```sh
python -m pip install -r requirements.txt
python -m pytest -q
python -m pip freeze > requirements.lock.txt
```

이 명령은 backend의 프로젝트 .venv에서 실행한다. 전역 환경의 freeze 결과를 덮어쓰지 않는다. 잠금 파일 변경을 검토한 뒤 백엔드 이미지를 다시 빌드한다.

## 로컬 프론트 의존성 — 선택 사항

```sh
cd frontend
npm ci
npm run typecheck
```

라이브러리 추가는 frontend에서 `npm install 패키지명`, 개발 전용 추가는 `npm install -D 패키지명`으로 수행한다. package.json과 package-lock.json을 함께 검토·커밋한다. 전역 설치를 사용하지 않는다. npm install은 의도적인 의존성 변경에, npm ci는 잠금 파일 그대로의 설치에 사용한다.

## VS Code 타입·import 오류

| 증상 | 확인할 것 |
|---|---|
| Python 라이브러리·stub을 못 찾음 | VS Code 인터프리터가 .venv 또는 개발 컨테이너인지 |
| Docker에서는 실행되는데 에디터가 import를 못 찾음 | 로컬 에디터와 컨테이너의 라이브러리 환경이 다를 수 있음 |
| JSX·이벤트 매개변수가 any로 표시됨 | frontend/node_modules, @types/react, tsconfig.json을 인식하는지 |
| 터미널 타입 검사와 에디터 결과가 다름 | TypeScript: Select TypeScript Version에서 워크스페이스 버전 선택 |

기존 검사에서 TSX 전체가 any인 문제는 재현되지 않았다. `useState("")`는 string으로, JSX 이벤트·배열 콜백은 props와 배열 원소 타입으로 추론된다. 타입 검사를 끄거나 any로 우회하지 않는다.

| 구분 | 타입 관리 기준 |
|---|---|
| 폼 제출 | FormEvent<HTMLFormElement> |
| DOM 참조 | useRef<HTMLDialogElement>(null) 등 실제 요소 타입 |
| 빈 선택값 | number 또는 null 등 유니언 |
| 인벤토리 | InventoryItem / InventoryData |
| 계정 | Account의 auth·user_status 리터럴 유니언 |
| 게시판 | Post / PostPage / PostInput / PostStatus |
| 성격·표현 | PersonalityKeyword / PersonalityCategory / ScriptOutput |
| API 오류 응답 | unknown에서 detail을 확인한 뒤 사용 |

## DB 스키마 버전 관리

운영 DB 구조는 Alembic으로 관리한다. 앱 기동은 최신 리비전 여부를 검사한다. production 초기화를 create_all로 수행하거나 과거 수동 migrate_character 파일을 실행하지 않는다.

1. 해당 기능의 models.py와 요청·응답 타입을 수정한다.
2. 새 리비전을 생성한다.
3. 생성 SQL과 데이터 변환을 검토한다.
4. 구 DB 업그레이드·데이터 보존·재실행을 검증한다.
5. 적용 후 앱을 시작한다.

백엔드 컨테이너에서 생성하는 예시:

```sh
docker compose exec backend alembic revision --autogenerate -m "describe change"
```

현재 Docker는 소스를 이미지에 복사한다. 위 명령으로 생긴 파일은 컨테이너 내부에 있으므로, 제거하기 전에 해당 파일을 호스트의 backend/alembic/versions로 복사해 Git으로 관리한다. 로컬 .venv와 DATABASE_URL을 준비했다면 backend 폴더에서 같은 alembic 명령을 실행해 호스트에 생성할 수도 있다.

이미 적용한 리비전의 로직을 바꾸지 않는다. 모델 수정만으로 기존 컬럼은 변하지 않는다. users 테이블 이전 이력의 client 명칭은 남긴다. DB 변경을 건너뛰기 위해 stamp head를 사용하지 않는다. 자동 downgrade를 막는 리비전이 있으므로 필요 시 백업 복원 또는 새 전진 리비전으로 처리한다.

## Git 버전 관리

| 종류 | 관리 대상 |
|---|---|
| 소스 | backend/app, frontend/app·components·hooks·lib·styles |
| DB 이력 | backend/alembic과 alembic.ini |
| 의존성 | requirements.txt·requirements.lock.txt, package.json·package-lock.json |
| 문서·소재 | 네 문서, 현재 사용하는 프로필 이미지 |
| 제외 | .env, node_modules, .next, .venv, __pycache__, 로컬 DB·덤프·비밀값 |

변경 범위를 확인하고 비밀 파일이 제외된 상태에서 커밋한다.

```sh
git status
git add README.md SETUP.md RUNNING.md RULE.md
git add -u -- '*.md'
git diff --cached --stat
git commit -m "docs: consolidate current project documentation"
```

`git add -u -- '*.md'`는 추적 중인 문서의 수정·삭제를 스테이징한다. 커밋 전 변경 목록을 확인한다.

기능 개발은 브랜치에서 진행하고 검증 후 main으로 병합한다. 릴리스 태그를 사용할 때는 실제 검증·배포한 버전만 지정한다. 현재 package.json의 0.1.0이 곧 운영 릴리스가 완료됐다는 뜻은 아니다.
