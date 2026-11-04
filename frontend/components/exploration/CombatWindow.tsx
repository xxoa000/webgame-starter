/* 메인 관측 화면 위에만 겹쳐지는 전투 창. 서브 콘솔의 인벤토리는 계속 사용할 수 있다. */
"use client";
import { ItemIndicators, itemFrame } from "../items/ItemIndicators";
import { classNames } from "../../lib/classNames";
import { useEffect, useId, useRef } from "react";
import styles from "./Observation.module.css";
import type { CombatState, ExplorationState } from "../../lib/exploration";
import { useExploration } from "../../hooks/useExploration";
import { CombatPanel } from "./CombatPanel";
import { ScriptLines } from "./ScriptLines";

export function CombatWindow({
  combat,
  disabled,
  loot = null,
}: {
  combat: CombatState | null;
  loot?: ExplorationState["pending_item"];
  disabled: boolean;
}) {
  /* 포털이나 새 브라우저 창 없이 메인 콘솔 안에서만 전투를 앞에 표시한다. */
  const game = useExploration();
  const latest = game.state?.history.at(-1);
  const titleId = useId();
  const windowRef = useRef<HTMLElement>(null);
  useEffect(() => {
    /* 조우 시 전투 창에 키보드 포커스를 두고 아이템 사용 중에는 포커스를 빼앗지 않는다. */
    windowRef.current?.focus({ preventScroll: true });
  }, [combat?.monster_id]);
  return (
    <div className={styles.combatOverlay}>
      <section
        ref={windowRef}
        className={styles.combatWindow}
        role="dialog"
        aria-modal="false"
        aria-labelledby={titleId}
        tabIndex={-1}
      >
        <header className={styles.combatWindowTitle}>
          <span>{loot ? "VICTORY / 전리품 회수" : "ENCOUNTER / 전투"}</span>
          <span aria-hidden="true">▣</span>
        </header>
        <div className={styles.combatWindowBody}>
          {combat && (
            <article className={styles.encounterCard}>
              <span className={styles.encounterLabel}>HOSTILE SIGNAL</span>
              <h2 id={titleId}>{combat.name}</h2>
              <p>{combat.description}</p>
              <div className={styles.combatHp}>
                <span>
                  HP {combat.hp} / {combat.max_hp}
                </span>
                <progress
                  value={combat.hp}
                  max={combat.max_hp}
                  aria-label="몬스터 HP"
                />
              </div>
            </article>
          )}
          {loot && (
            <div
              className={classNames(styles.combatLoot, itemFrame(loot.rarity))}
            >
              <ItemIndicators rarity={loot.rarity} edible={loot.edible} />
              <h2 id={titleId}>전투 승리</h2>
              <h3>{loot.name}</h3>
              <p>{loot.description}</p>
              <small>
                ×{loot.quantity} · {(loot.weight_grams * loot.quantity) / 1000}{" "}
                kg
              </small>
            </div>
          )}
          <div className={styles.combatReport} aria-live="polite">
            <p className={styles.turnMessage}>{latest?.message}</p>
            <ScriptLines outputs={latest?.scripts} />
          </div>
          {game.error && <p role="alert">{game.error}</p>}
          {loot ? (
            <div className={styles.explorationActions}>
              <button disabled={disabled} onClick={() => void game.act("take")}>
                회수
              </button>
              <button
                disabled={disabled}
                onClick={() => void game.act("give_up")}
              >
                포기
              </button>
              <button
                disabled={game.busy}
                aria-expanded={game.window === "inventory"}
                onClick={() =>
                  game.setWindow(
                    game.window === "inventory" ? null : "inventory",
                  )
                }
              >
                아이템
              </button>
            </div>
          ) : (
            <CombatPanel disabled={disabled} />
          )}
        </div>
      </section>
    </div>
  );
}
