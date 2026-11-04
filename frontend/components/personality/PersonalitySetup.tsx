/* 기존 캐릭터의 비어 있는 성격을 최초 한 번 확정한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import { useState } from "react";
import { useGame } from "../../hooks/useGame";
import { PersonalityPicker } from "./PersonalityPicker";
export function PersonalitySetup() {
  /* 캐릭터 생성 이전 버전의 사용자가 직접 세 분류를 선택하게 한다. */
  const game = useGame();
  const [ids, setIds] = useState<number[]>([]);
  return (
    <section
      className={sharedStyles.panel}
      data-ui="panel"
    >
      <h2>성격 선택</h2>
      <PersonalityPicker
        value={ids}
        onChange={setIds}
        disabled={game.busy}
      />
      <button
        className={sharedStyles.primaryButton}
        disabled={game.busy || ids.length !== 3}
        onClick={() => {
          return void game.run(() => {
            return game.selectPersonality(ids);
          });
        }}
        data-ui="primaryButton"
      >
        성격 확정
      </button>
    </section>
  );
}
