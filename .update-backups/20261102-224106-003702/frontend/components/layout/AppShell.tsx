"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type Props = { username?: string; ready: boolean; children: ReactNode };

export function AppShell({ username, ready, children }: Props) {
  const exploring = usePathname().startsWith("/explore");
  return (
    <div className="shell">
      <aside>
        <a className="logo" href="/">
          O<span>RIGIN</span>
          <i>●</i>
        </a>
        <div className="workspace">YOUR WORKSPACE</div>
        <nav className="game-nav">
          <Link
            href="/"
            className={`menu-link ${!exploring ? "active" : ""}`}
            aria-current={!exploring ? "page" : undefined}
          >
            ◈ <span>캐릭터 아카이브</span>
          </Link>
          <Link
            href="/explore"
            className={`menu-link ${exploring ? "active" : ""}`}
            aria-current={exploring ? "page" : undefined}
          >
            ⌕ <span>숲 탐색</span>
          </Link>
        </nav>
        <div className="aside-bottom">
          <span className="status-dot" /> 새로운 이야기의 시작
          <br />
          <small>WORLD UNDEFINED · FOUNDATION 01</small>
        </div>
      </aside>
      <main>
        <header>
          <span>
            WORKSPACE <b>/</b>{" "}
            {exploring ? "FOREST EXPLORATION" : "CHARACTER ARCHIVE"}
          </span>
          <div>{username ? `${username} 님` : "아직 쓰이지 않은 이야기"}</div>
        </header>
        <section className="heading">
          <div className="eyebrow">
            {exploring
              ? "A SMALL DISCOVERY, A NEW POSSIBILITY"
              : "MAKE YOUR FIRST CHAPTER"}
          </div>
          <h1>
            {exploring
              ? "숲이 품은 가능성을 찾아."
              : !username
                ? "이야기는, 여기서 시작돼."
                : ready
                  ? "나의 캐릭터 아카이브."
                  : "가능성을 발견하는 시간."}
          </h1>
          <p>
            {exploring
              ? "작은 채집에서 시작해, 마나를 다루는 법을 배워가는 이야기."
              : !username
                ? "계정을 만들고, 너만의 캐릭터로 새로운 세계를 준비해."
                : ready
                  ? "네가 선택한 캐릭터의 프로필과 능력치를 한눈에 확인해."
                  : "우연이 만든 능력치에, 네가 고른 이름과 개성을 더해."}
          </p>
        </section>
        {children}
        <footer>
          ORIGIN ARCHIVE <span>너의 다음 이야기를 기다리는 중.</span>
        </footer>
      </main>
    </div>
  );
}
