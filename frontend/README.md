# 프론트엔드 스타일 관리

Next.js에 기본으로 포함된 CSS Modules를 사용한다. Tailwind나 별도의 런타임 스타일 라이브러리는 설치하지 않는다. 기존 API 주소, 포트, 인증 방식과 게임 규칙은 유지한다.

## 적용

기존 프로젝트 최상위에 ZIP을 병합한다. 폴더 전체를 삭제하거나 교체하지 않는다. 환경 파일은 압축에 포함하지 않는다.

```bash
cd frontend
npm ci
npm run cleanup:styles
npm run dev
```

`cleanup:styles`는 이번 작업으로 사용하지 않게 된 기존 CSS 파일만 목록에 따라 제거한다. 환경 파일, 이미지, 코드, 새 CSS Modules는 제거하지 않는다. 이미 정리했다면 다시 실행해도 된다.

개발 서버 포트는 기존 설정인 5174다. Docker 프론트가 같은 포트를 사용 중이라면 먼저 해당 컨테이너를 중지한다. 백엔드는 기존 실행 상태와 API 설정을 사용한다.

## 파일 계층

| 위치                                            | 관리하는 내용                                     |
| ----------------------------------------------- | ------------------------------------------------- |
| `app/globals.css`                               | 전역 테마·기본 요소 스타일의 진입점               |
| `styles/shared/tokens.css`                      | 공통 색상·글꼴·모서리 크기의 기본값               |
| `styles/shared/base.css`                        | body·버튼·입력 요소·접근성 기본값                 |
| `styles/shared/Controls.module.css`             | 공통 패널·버튼·안내 문구                          |
| `components/console/Console.module.css`         | 모니터 외장·공통 헤더·서브 콘솔·물리 버튼         |
| `components/home/Home.module.css`               | 공지·재난 경보·기관 소개                          |
| `components/auth/Auth.module.css`               | 로그인·회원가입                                   |
| `components/characters/Characters.module.css`   | 캐릭터 등록·프로필·성격·HP/MP/스태미나            |
| `components/exploration/Exploration.module.css` | 지도·행동 패널·전투·구조·인벤토리·도감            |
| `components/posts/Posts.module.css`             | 게시판                                            |
| `components/shop/Shop.module.css`               | 보급 상점                                         |
| `styles/loadStyles.ts`                          | 화면 이동과 관계없이 모듈 스타일의 로딩 순서 유지 |
| `lib/classNames.ts`                             | 조건에 따라 여러 모듈 클래스를 결합               |

프로필 이미지 선택과 성격 선택도 캐릭터 기능이므로 `Characters.module.css`를 공유한다. 인벤토리와 도감은 서브 콘솔에서도 사용하지만 항목의 실제 모양은 `Exploration.module.css`에서 관리한다.

## TSX와 CSS 연결

```tsx
import styles from "./Exploration.module.css";

<div className={styles.mapHeading}>
  <h2>균열 탐색</h2>
</div>;
```

```css
.mapHeading {
  position: absolute;
  top: 20px;
  left: 22px;
}
```

`styles.mapHeading`은 같은 폴더의 CSS 파일에 있는 `.mapHeading`을 가리킨다. 빌드할 때 고유한 이름으로 바뀌므로 다른 화면에서 같은 이름을 사용해도 충돌하지 않는다. 다른 파일에서 만든 클래스를 문자열로 그대로 쓰지 않는다.

여러 클래스나 조건부 스타일은 `classNames`로 결합한다.

```tsx
className={classNames(styles.hardwareMenu, active && styles.isActive)}
```

이 함수는 빈 값을 제외하고 클래스 이름을 연결할 뿐이다. API 요청이나 게임 상태 변경은 하지 않는다.

## 이름을 찾는 기준

| 이름             | 의미                              |
| ---------------- | --------------------------------- |
| `mapViewport`    | 지도 전체 영역                    |
| `mapHeading`     | 지도 제목과 설명                  |
| `mapStatus`      | 온라인 인원·턴 표시               |
| `actionArea`     | 지도 아래 행동 영역               |
| `actionHeader`   | 탐색 상태와 동행 드론의 공통 헤더 |
| `companionDrone` | 동행 드론 표시                    |
| `itemSlot`       | 인벤토리·도감 한 칸               |
| `thoughtBubble`  | 서브 콘솔 속마음 말풍선           |
| `primaryButton`  | 주요 행동 버튼                    |
| `helpText`       | 보조 안내 문구                    |

## 다른 모듈 안에 배치되는 요소

인벤토리·자원 바처럼 여러 화면에서 재사용하는 요소는 부모 배치에 따라 크기가 달라진다. 이 연결에만 `data-ui`를 사용한다.

```tsx
<div className={styles.subConsoleContent} data-ui="subConsoleContent">
```

다른 모듈에서는 다음처럼 부모를 확인할 수 있다.

```css
:global([data-ui~="subConsoleContent"]) .resourceBars {
  margin-top: 16px;
}
```

`data-ui`는 화면에 보이지 않는 스타일 연결 표식이다. 로그인 권한이나 데이터 처리와는 무관하다. `:global`은 이 표식을 모듈의 고유 클래스 이름으로 변환하지 말라는 뜻이며, 실제 적용 대상인 `.resourceBars`는 모듈 안에 격리된다. 재사용 배치를 유지하려면 기존 표식을 임의로 삭제하지 않는다.

## 수정 규칙

1. 컴포넌트 상단의 CSS import를 확인하고 해당 모듈에서 수정한다.
2. 기존 선택자가 있으면 그 규칙을 고친다. 파일 끝에 같은 선택자를 계속 추가하지 않는다.
3. `@media`는 화면 너비 조건이다. 같은 선택자라도 화면 조건이 다르면 별도의 규칙일 수 있다.
4. 모든 화면에서 쓰는 값만 공통 토큰에 둔다. 한 화면에만 쓰는 값을 전역 CSS에 넣지 않는다.
5. 주석은 타이머 정리, 서버 검증, 모듈 간 연결처럼 이유가 필요한 부분에만 쓴다.

## 검사와 자동 정렬

```bash
npm run check:styles
npm run typecheck
npm run format:check
npm run build
```

수정한 코드를 자동 정렬하려면 다음 명령을 사용한다.

```bash
npm run format
```

Prettier는 개발용 도구다. 80자 기준 줄바꿈, 공백 2칸 들여쓰기, JSX 속성별 줄바꿈을 프로젝트 설정으로 고정했다. 긴 문자열·SVG 경로·정규식은 의미가 바뀌지 않도록 필요한 경우 그대로 둔다.

이번 정리에서는 타입 검사, CSS 연결 검사와 Next.js 프로덕션 빌드를 확인한다. 실제 브라우저에서 화면 크기별 시각 비교는 이 실행 환경의 브라우저 제한으로 수행하지 못했다.
