/* 피계약자 인증 상태를 확인하고 붉은 테마의 균열 탐색 화면을 연다. */
"use client";
import Link from "next/link";
import { DeathRecord } from "../../components/characters/DeathRecord";
import { useGame } from "../../hooks/useGame";
import { AppShell } from "../../components/layout/AppShell";
import { ExplorationWorkspace } from "../../components/exploration/ExplorationWorkspace";

export default function ExplorePage() {
  /* 계정과 캐릭터 상태에 맞는 탐색 화면을 표시한다. */

  const game = useGame();
  const character = game.account?.character;
  return (
    <AppShell
      username={game.account?.username}
      ready={character?.status === "ready"}
      auth={game}
    >
      {game.loading ? (
        <div className="panel">피계약자 신원을 확인하는 중…</div>
      ) : character?.status === "dead" ? (
        <DeathRecord />
      ) : character?.status === "ready" &&
        character.personality.length !== 3 ? (
        <section className="panel">
          <h2>성격 선택이 필요해.</h2>
          <Link href="/character">캐릭터 메뉴로 →</Link>
        </section>
      ) : character?.status === "ready" ? (
        <ExplorationWorkspace
          key={character.id}
          character={character}
          ranges={game.ranges}
        />
      ) : (
        <section className="panel empty">
          <h2>현장 투입 전 등록이 필요합니다.</h2>
          <p>
            {game.account
              ? "먼저 피계약자 등록을 완료하십시오."
              : "주무관 인증 후 피계약자를 등록하십시오."}
          </p>
          <Link href="/character" className="explore-home-link">
            피계약자 관리로 →
          </Link>
        </section>
      )}
    </AppShell>
  );
}
