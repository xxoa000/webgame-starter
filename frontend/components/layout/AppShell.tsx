/* 메인 작업 화면의 기관 로고·인증 상태·페이지 제목을 표시한다. 인증 입력은 서브콘솔에서 처리한다. */
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import type { useGame } from "../../hooks/useGame";
import { AGENCY } from "../../lib/world";

type Props = {
  username?: string;
  ready: boolean;
  children: ReactNode;
  auth: ReturnType<typeof useGame>;
};
export function AppShell({ username, ready, children, auth }: Props) {
  /* 페이지 제목과 기관 공통 외곽 화면을 구성한다. */

  const pathname = usePathname();
  const exploring = pathname.startsWith("/explore");
  const home = pathname === "/";
  const posts = pathname.startsWith("/posts");
  const about = pathname === "/about";
  return (
    <div
      className={`shell bureau-shell ${exploring ? "field-terminal" : "control-terminal"}`}
    >
      <main className="bureau-main">
        <header className="bureau-header">
          <Link
            href="/"
            className="console-brand"
            aria-label="차원위상격리감시국 홈"
          >
            <span className="agency-mark">⟐</span>
            <span>{AGENCY}</span>
          </Link>
          <span>
            상황관제탑 <b>/</b>{" "}
            {posts
              ? "게시판"
              : home
                ? "통합 관제 단말"
                : exploring
                  ? "현장 원격 관제"
                  : about
                    ? "기관 소개"
                    : "피계약자 관리"}
          </span>
          <div className="operator-badge">
            <span className="status-dot" />
            {username ? `주무관 ${username}` : "인증 대기"}
          </div>
        </header>
        {!home && !posts && (
          <section className="heading">
            <div>
              <div className="eyebrow">
                {about
                  ? "BUREAU ORGANIZATION"
                  : exploring
                    ? "REMOTE FIELD OPERATIONS"
                    : "CONTRACTOR MANAGEMENT"}
              </div>
              <h1>
                {about
                  ? "기관 소개"
                  : exploring
                    ? "균열 탐색 관제"
                    : !username
                      ? "피계약자 관리"
                      : ready
                        ? "피계약자 관리"
                        : "신규 피계약자 등록"}
              </h1>
              <p>
                {about
                  ? "균열을 관측하고, 현장에 대응하며, 현실을 지키는 네 개의 기관입니다."
                  : exploring
                    ? "중계 드론을 통해 현장을 관측하고, 피계약자의 다음 행동을 지시합니다."
                    : !username
                      ? "오른쪽 하단 인증 버튼으로 로그인한 뒤 피계약자를 관리하십시오."
                      : ready
                        ? "현장대응센터 소속 피계약자의 신원과 현재 상태를 확인합니다."
                        : "첫 투입은 민간인으로 시작합니다. 신원과 초기 능력을 등록하십시오."}
              </p>
            </div>
          </section>
        )}
        {children}
        <footer>
          <span>
            {AGENCY} <b> / </b> 상황관제탑
          </span>
          <span>원격으로 연결된 두 세계.</span>
        </footer>
      </main>
    </div>
  );
}
