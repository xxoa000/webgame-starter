/* 사망 기록과 새 피계약자 등록 진입점을 표시한다. */
"use client";
import { useGame } from "../../hooks/useGame";
import { PixelCharacter } from "../appearance/PixelCharacter";
export function DeathRecord() {
  /* 화면 상태를 확인하고 DeathRecord 기능을 실행한다. */

  const game = useGame();
  const character = game.account?.character;
  if (character?.status !== "dead") return null;
  return (
    <section className="panel death-record">
      <h2>피계약자 사망</h2>
      <div className="death-portrait">
        <PixelCharacter appearance={character.appearance} />
      </div>
      <h3>{character.name}</h3>
      <p>HP 0 · 연결 종료</p>
      <button
        className="primary"
        disabled={game.busy}
        onClick={() => {
          /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.run(
            game.startCharacter,
          );
        }}
      >
        새 피계약자 등록
      </button>
    </section>
  );
}
