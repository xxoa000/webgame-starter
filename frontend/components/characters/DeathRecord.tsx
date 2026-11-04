/* 사망 기록과 새 피계약자 등록 진입점을 표시한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Characters.module.css";
import { classNames } from "../../lib/classNames";
import { useGame } from "../../hooks/useGame";
import { PixelCharacter } from "../appearance/PixelCharacter";
export function DeathRecord() {
  /* 사망 기록과 새 캐릭터 생성 버튼을 표시한다. */

  const game = useGame();
  const character = game.account?.character;
  if (character?.status !== "dead") return null;
  return (
    <section
      className={classNames(sharedStyles.panel, styles.deathRecord)}
      data-ui="panel"
    >
      <h2>피계약자 사망</h2>
      <div className={styles.deathPortrait}>
        <PixelCharacter appearance={character.appearance} />
      </div>
      <h3>{character.name}</h3>
      <p>HP 0 · 연결 종료</p>
      <button
        className={sharedStyles.primaryButton}
        disabled={game.busy}
        onClick={() => {
          return void game.run(game.startCharacter);
        }}
        data-ui="primaryButton"
      >
        새 피계약자 등록
      </button>
    </section>
  );
}
