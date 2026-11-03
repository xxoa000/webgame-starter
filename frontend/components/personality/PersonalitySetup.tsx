/* 기존 캐릭터의 비어 있는 성격을 최초 한 번 확정한다. */
"use client";
import { useState } from "react";
import { useGame } from "../../hooks/useGame";
import { PersonalityPicker } from "./PersonalityPicker";
export function PersonalitySetup() {
  /* 캐릭터 생성 이전 버전의 사용자가 직접 세 분류를 선택하게 한다. */
  const game = useGame();
  const [ids, setIds] = useState<number[]>([]);
  return (
    <section className="panel">
      <h2>성격 선택</h2>
      <PersonalityPicker value={ids} onChange={setIds} disabled={game.busy} />
      <button
        className="primary"
        disabled={game.busy || ids.length !== 3}
        onClick={() => {
          /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return void game.run(
            () => {
              /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return game.selectPersonality(
                ids,
              );
            },
          );
        }}
      >
        성격 확정
      </button>
    </section>
  );
}
