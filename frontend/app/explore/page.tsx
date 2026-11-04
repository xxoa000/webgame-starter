/* 피계약자 인증 상태를 확인하고 붉은 테마의 균열 탐색 화면을 연다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "../../components/exploration/Exploration.module.css";
import { classNames } from "../../lib/classNames";
import Link from "next/link";
import { DeathDebrief } from "../../components/exploration/DeathDebrief";
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
        <div
          className={sharedStyles.panel}
          data-ui="panel"
        >
          피계약자 신원을 확인하는 중…
        </div>
      ) : character?.status === "dead" ? (
        <DeathDebrief />
      ) : character?.status === "ready" &&
        character.personality.length !== 3 ? (
        <section
          className={sharedStyles.panel}
          data-ui="panel"
        >
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
        <section
          className={classNames(sharedStyles.panel, sharedStyles.empty)}
          data-ui="panel"
        >
          <h2>현장 투입 전 등록이 필요합니다.</h2>
          <p>
            {game.account
              ? "먼저 피계약자 등록을 완료하십시오."
              : "주무관 인증 후 피계약자를 등록하십시오."}
          </p>
          <Link
            href="/character"
            className={styles.exploreHomeLink}
          >
            피계약자 관리로 →
          </Link>
        </section>
      )}
    </AppShell>
  );
}
