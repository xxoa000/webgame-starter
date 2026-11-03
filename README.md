# 차원위상격리감시국

주무관이 원격 관제 단말을 통해 피계약자를 조종하고, 붕괴한 세계의 균열을 탐색하는 웹게임이다. 검정·회색 기반 레트로 콘솔 UI 안에 계정, 캐릭터, 탐색, 전투와 성격별 스크립트를 구성한다.

이 문서는 `0011_personality_scripts`까지 적용한 최신 코드를 기준으로 한다. 과거 패치별 적용 안내 대신 아래 네 문서를 사용한다.

| 문서 | 내용 |
|---|---|
| [README.md](README.md) | 프로젝트 설명, 처리 흐름, 폴더·모듈·DB 구조 |
| [SETUP.md](SETUP.md) | 의존성 설치, 가상환경, 라이브러리·Git·마이그레이션 버전 관리 |
| [RUNNING.md](RUNNING.md) | 초기 실행, 재실행, 업데이트, 로그·포트·문제 확인 |
| [RULE.md](RULE.md) | 현재 구현된 게임 기능과 계산·권한 규칙 |

## 기술 구성

| 영역 | 구성 |
|---|---|
| 프론트엔드 | Next.js App Router, React, TypeScript |
| 백엔드 | FastAPI, Uvicorn, Pydantic, SQLAlchemy 동기 세션 |
| DB | MySQL 8.4, PyMySQL, Alembic |
| 인증 | Argon2 비밀번호 해시, 서버 세션·HttpOnly 쿠키 |
| 실행 | Docker Compose: mysql / backend / frontend |
| 테스트 | pytest, FastAPI TestClient, 격리된 SQLite DB |
| Redis | 현재 도입하지 않음. 향후 공통 조회 후보 캐시 용도로 검토 |

## 구현 상태

| 영역 | 현재 상태 |
|---|---|
| 계정 | 가입·중복 확인·로그인·로그아웃·휴면 재활성화·권한/상태 검사 |
| 캐릭터 | 생성·전체 재추첨·프로필 프리셋·인적사항 수정·관리자 삭제·사망 보관 |
| 성격 | 겉성격·속성격·성향에서 각 1개 선택, 기존 캐릭터 최초 선택 지원 |
| 탐색 | 맵 8개, 파밍 물자 24종, 확률 조우·선택·DB 상태 유지 |
| 전투 | 몬스터 8종, 공격·확정 도망·회복 물자·부상·사망·전리품 |
| 인벤토리·도감 | 10종·30kg 제한, 발견 기록과 미확인 이름 처리 |
| 스크립트 | 초기 178개, 조건·우선순위·가중 추첨·출력 스냅샷·사용권 검사 |
| 게시판 | CRUD·공지·운영 상태 관리·권한별 제어 |
| 균열 경보 | 홈 표시 UI. 일정 데이터는 frontend/lib/control.ts에서 관리 |
| 원고 작성·심사·묶음 사용권 | 테이블 기반과 선택 엔진만 준비. 사용자 관리 화면/API는 아직 없음 |
| 상점·재화·유료 결제·온라인 조우 | 아직 구현하지 않음 |
| 마법·제작 | grimoire·recipe 테이블만 준비. 실제 사용 기능은 아직 없음 |

## 요청 처리 파이프라인

| 순서 | 담당 | 처리 |
|---|---|---|
| 1 | page / component | 사용자의 입력과 행동을 받는다 |
| 2 | hook → lib/api.ts | 공유 상태를 관리하고 인증 쿠키와 JSON 요청을 전송한다 |
| 3 | router / schemas | 경로·로그인·입력 형식을 검사한다 |
| 4 | service / policy | 소유권·권한·게임 규칙·수정 한도를 검사한다 |
| 5 | repository / SQLAlchemy | 필요한 행을 조회·잠금하고 변경한다 |
| 6 | service | 결과·보관 기록을 같은 트랜잭션에서 커밋한다 |
| 7 | API 응답 → hook → component | 서버 결과로 화면과 공유 상태를 갱신한다 |

탐색은 프론트 타이머가 자동 진행하는 방식이 아니다. 사용자의 명령마다 서버가 턴을 처리한다. 탐색 버전 번호와 DB 행 잠금으로 오래된 요청·중복 변경을 제어한다. 대사 추첨은 게임 결과에 표현을 덧붙이며 피해나 아이템 지급을 변경하지 않는다.

## 최상위 폴더

| 경로 | 역할 |
|---|---|
| backend/app/main.py | 앱 생성, 라우터 등록, 출처 검사, 휴면 작업 수명 |
| backend/app/core/ | 설정·인증·공통 의존성 |
| backend/app/database/ | 공통 Base·감사 시각·연결·모델 등록·리비전 검사 |
| backend/app/modules/ | 기능별 모델·스키마·라우터·서비스·저장소 |
| backend/alembic/versions/ | DB 변경 이력. 최신 head는 0011_personality_scripts |
| backend/tests/ | API·게임 규칙·마이그레이션·보존성 테스트 |
| backend/requirements.txt | 직접 사용하는 라이브러리의 허용 버전 범위 |
| backend/requirements.lock.txt | Docker 설치에 사용하는 고정 버전 |
| frontend/app/ | /, /about, /character, /explore, /posts 라우트 |
| frontend/components/ | 화면의 기능별 컴포넌트 |
| frontend/hooks/ | 계정·캐릭터·탐색·게시판 공유 상태와 요청 |
| frontend/lib/ | API, 타입, 스탯 표시, 프리셋, 기관·이벤트 정의 |
| frontend/styles/bureau/ | 현재 콘솔 테마와 기능별 CSS |
| frontend/app/globals.css | 실제 사용하는 CSS import 목록 |
| frontend/public/portraits/ | 선택 가능한 완성형 프로필 PNG 6장 |
| frontend/package.json / package-lock.json | npm 실행 명령·의존성·잠금 버전 |
| scripts/start.py | .env를 저장하지 않고 실행 환경에 포트 선택값을 전달하는 보조 도구 |
| compose.yaml | 서비스·볼륨·빌드·포트 연결 정의 |

이전 스타일·스프라이트 파일이 남아 있을 수 있지만 현재 사용 여부는 import와 참조 경로로 판단한다. 이번 문서 정리에서는 소스·소재 파일을 삭제하지 않는다.

## 백엔드 모듈과 수정 위치

| 모듈/파일 | 담당 |
|---|---|
| users | 계정·세션·권한·휴면·로컬 운영 명령 |
| characters | 생성·프로필·이름·수정 기회·삭제 보관·자원 |
| characters/rules.py | 스탯 합계·최대 재추첨·자원 배율·회복 간격 |
| characters/stats.py | 합계 20인 스탯 분배 |
| personality | 키워드·선택 검증·초기 시드 참고 |
| scripts | 묶음·버전·조건·사용권과 대사 선택 |
| maps / items | 맵과 공통 아이템 정의·연결 |
| exploration | 탐색 상태·턴·회수 선택·결과 기록 |
| combat | 조우·공격·전리품·사망·회복 물자 규칙 |
| inventory / encyclopedia | 보유 물자·용량과 최초 발견 기록 |
| posts | 게시판과 공지 CRUD·권한·정렬 |
| monsters / magic / recipes | 몬스터·마법·조합 모델 |

모든 모듈이 다섯 파일을 반드시 채우는 것은 아니다. 현재 모델만 필요한 기능에는 아직 라우터나 서비스가 없다. models.py는 저장 구조, schemas.py는 API 형식, router.py는 경로, service.py는 규칙·커밋, repository.py는 조회를 맡는다.

## 프론트 수정 위치

| 경로 | 담당 |
|---|---|
| components/console/ | 메인·서브 콘솔, 하단 물리 메뉴, 공통 프로필 |
| components/home/NoticeBoard.tsx | DB 공지 표시 |
| components/home/RiftAlert.tsx | 홈의 균열 경보 표시 |
| components/characters/ | 생성·프로필·인적사항·자원·사망·삭제 확인 |
| components/personality/ | 분류별 키워드 선택·기존 캐릭터 설정 |
| components/appearance/ | 프로필 프리셋 선택 |
| components/exploration/ | 탐색 선택지·전투·대사·도감 |
| components/inventory/ | 가로형 인벤토리 |
| components/posts/ | 게시판 목록·본문·편집 |
| hooks/useGame.ts | 계정·캐릭터 상태와 등록·수정 요청 |
| hooks/useExploration.ts | 탐색·인벤토리·보조 창 공유 |
| hooks/usePosts.ts | 게시판 조회·선택·변경 |
| lib/types.ts / exploration.ts / personality.ts / posts.ts | 공통 API 타입 |

## DB 구성

현재 애플리케이션 테이블은 28개이며 Alembic 관리 테이블은 별도다.

| 분류 | 테이블 |
|---|---|
| 계정 | users, login_session |
| 캐릭터 | character, deleted_character |
| 성격 | personality_keyword, character_personality |
| 맵·아이템 | map, item, farming_item, drop_item, map_farming_item |
| 몬스터 | monster, map_monster, monster_drop_item |
| 인벤토리·탐색 | inventory, inventory_entry, exploration, encyclopedia |
| 확장용 | grimoire, recipe |
| 게시판 | posts |
| 대사 | script_pack, script_pack_version, game_script, game_script_condition |
| 기여·사용권 기반 | script_submission, user_script_pack, character_script_pack |
| 마이그레이션 관리 | alembic_version |

모든 테이블에 create_at·update_at을 두고 컬럼 COMMENT를 정의한다. MySQL의 update_at은 ON UPDATE CURRENT_TIMESTAMP를 사용한다. 백엔드 연결 시각은 UTC다. 기존 행의 알 수 없는 과거 시각은 감사 컬럼 추가 시점의 값으로 채웠다.

사용자 테이블은 users다. 과거 리비전의 client는 과거 DB를 재현하기 위한 이력이므로 일괄 치환하지 않는다. 캐릭터의 성격은 분류별 유일성과 복합 FK로 분류 일치를 검사한다. 상세 규칙은 [RULE.md](RULE.md), DB 변경 방법은 [SETUP.md](SETUP.md)를 참고한다.

## 소재와 UI

현재 프로필은 참고 이미지의 분위기를 반영해 생성한 저채도 완성형 PNG 6장이다. 이미지를 그대로 표시하며 색상 변환·전신 모션·8방향 회전은 사용하지 않는다. 파일과 선택 매핑은 frontend/public/portraits/와 frontend/lib/appearance.ts에 있다.

로그인은 서브 콘솔, 프로필 상세는 메인 콘솔에 표시한다. 인벤토리·도감은 메인 콘솔 하단 보조 영역을 사용한다. 보조 창 열기와 페이지 이동은 탐색 턴을 진행하거나 상태를 초기화하지 않는다.

## 코드 작성 기준

Python 파일 상단·함수 첫 부분에는 docstring, TSX 파일 상단·함수 내부에는 설명 주석을 둔다. 화면에는 필요한 안내만 표시한다. TypeScript strict 검사를 유지하고, 정상 추론되는 상태·콜백에 불필요한 any를 붙이지 않는다. 기능 변경 시 해당 서비스·스키마·타입·마이그레이션을 함께 확인한다.
