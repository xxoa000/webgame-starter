/* 전투 선택지와 회복 아이템 사용 창을 표시한다. 아이템은 턴을 쓰지 않는다. */
"use client";

import styles from "./Observation.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import { useExploration } from "../../hooks/useExploration";
export function CombatPanel({
  disabled,
  outsideCombat = false,
}: {
  disabled: boolean;
  outsideCombat?: boolean;
}) {
  /* 몬스터 정보는 결과 창 오른쪽에서 표시하고 이곳에는 버튼만 둔다. */
  const game = useExploration();
  return (
    <div className={styles.combatPanel}>
      <div className={styles.explorationActions}>
        {!outsideCombat && (
          <>
            <button
              className={sharedStyles.primaryButton}
              disabled={disabled}
              onClick={() => {
                /* 공격과 반격을 한 턴 진행한다. */ void game.act("fight");
              }}
              data-ui="primaryButton"
            >
              전투
            </button>
            <button
              disabled={disabled}
              onClick={() => {
                /* 확정 도망을 실행한다. */ void game.act("flee");
              }}
            >
              도망
            </button>
          </>
        )}
        <button
          disabled={game.busy || !!game.state?.downed}
          aria-expanded={game.window === "inventory"}
          onClick={() => {
            /* 물품 버튼을 다시 누르면 같은 창을 닫는다. */ game.setWindow(
              game.window === "inventory" ? null : "inventory",
            );
          }}
        >
          아이템
        </button>
      </div>
    </div>
  );
}
