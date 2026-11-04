/* 초기 능력치 재추첨과 구매한 미분배 스탯 포인트의 분배를 관리한다. */
"use client";
import { useEffect, useRef, useState } from "react";
import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Characters.module.css";
import { classNames } from "../../lib/classNames";
import { ResourceBars } from "./ResourceBars";
import type { Character, StatRanges } from "../../lib/types";
import { CORE_STATS, STAT_LABELS, STAT_ORDER } from "../../lib/stats";
import { useGame } from "../../hooks/useGame";
import { api } from "../../lib/api";
type Props = {
  character: Character;
  ranges: StatRanges;
  busy: boolean;
  reroll: () => void;
};
export function StatsPanel({ character, ranges, busy, reroll }: Props) {
  /* 확정 전 분배안만 +/-로 조정하고 적용할 때 서버 버전과 잔여 포인트를 검증한다. */
  const game = useGame();
  const [allocation, setAllocation] = useState<Record<string, number>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const ready = character.status === "ready";
  const assigned = Object.values(allocation).reduce(
    (sum, value) => sum + value,
    0,
  );
  const remaining = (character.stat_points ?? 0) - assigned;
  const disabled = busy || saving || character.downed;
  useEffect(() => {
    /* 서버에서 포인트 구매·분배가 반영되면 이전 임시 분배안을 비운다. */
    setAllocation({});
  }, [character.id, character.stat_version]);
  const total = CORE_STATS.reduce(
    (sum, key) => sum + (character.stats[key] ?? 0) + (allocation[key] ?? 0),
    0,
  );
  function adjust(key: string, step: number) {
    /* 기존 능력치를 낮추지 않고 아직 확정하지 않은 포인트만 되돌린다. */
    if (
      disabled ||
      (step > 0 && remaining <= 0) ||
      (step < 0 && !allocation[key])
    )
      return;
    setAllocation((previous) => ({
      ...previous,
      [key]: (previous[key] ?? 0) + step,
    }));
  }
  async function apply() {
    /* 중복 클릭과 버전 재사용을 차단해 한 번만 분배한다. */
    if (pending.current || assigned < 1) return;
    pending.current = true;
    setSaving(true);
    setError("");
    try {
      await api<Character>("/characters/stats/allocate", {
        version: character.stat_version ?? 0,
        ...allocation,
      });
      await game.reloadAccount();
    } catch (error) {
      setError(error instanceof Error ? error.message : "분배 실패");
      await game.reloadAccount().catch(() => {});
    } finally {
      pending.current = false;
      setSaving(false);
    }
  }
  return (
    <section
      className={classNames(sharedStyles.panel, styles.stats)}
      data-ui="panel"
    >
      <div className={styles.statTitle}>
        <div>
          <div className={sharedStyles.smallLabel} data-ui="smallLabel">
            {ready ? "CAPABILITY REPORT" : "02 / 초기 능력 평가"}
          </div>
          <h2>현장 능력 평가</h2>
        </div>
        {ready ? (
          <span className={styles.statPoints} role="status">
            남은 포인트 {remaining}
          </span>
        ) : (
          <span className={styles.badge}>평가 중</span>
        )}
      </div>
      {!ready && (
        <p className={sharedStyles.mutedText} data-ui="mutedText">
          기본 스탯 5개의 합계는 20이야.
        </p>
      )}
      {ready && <ResourceBars vitals={character.vitals} />}
      <div className={styles.statList}>
        {STAT_ORDER.map((key) => {
          /* 구매 보너스는 초기 생성 범위를 넘어 올릴 수 있다. */
          const value = character.stats[key] + (allocation[key] ?? 0);
          const [minimum, maximum] = ranges[key] ?? [1, 16];
          const width = Math.max(
            2,
            Math.min(
              100,
              ((value - minimum) / Math.max(1, maximum - minimum)) * 100,
            ),
          );
          return (
            <div className={styles.stat} key={key}>
              <div>
                <span>{STAT_LABELS[key]}</span>
                {!ready && (
                  <small>
                    {minimum}–{maximum}
                  </small>
                )}
                {ready ? (
                  <span className={styles.statControls}>
                    <button
                      type="button"
                      aria-label={`${STAT_LABELS[key]} 감소`}
                      disabled={disabled || !(allocation[key] > 0)}
                      onClick={() => adjust(key, -1)}
                    >
                      −
                    </button>
                    <strong>{value}</strong>
                    <button
                      type="button"
                      aria-label={`${STAT_LABELS[key]} 증가`}
                      disabled={disabled || remaining <= 0}
                      onClick={() => adjust(key, 1)}
                    >
                      +
                    </button>
                  </span>
                ) : (
                  <strong>{value}</strong>
                )}
              </div>
              <div className={styles.track}>
                <div style={{ width: `${width}%` }} />
              </div>
            </div>
          );
        })}
      </div>
      <div className={styles.statTotal}>
        <span>스탯 합계</span>
        <strong>
          {total}
          {!ready && <small> / 20</small>}
        </strong>
      </div>
      {ready && (
        <div className={styles.statApply}>
          <button
            disabled={disabled || assigned < 1}
            onClick={() => void apply()}
          >
            분배 적용
          </button>
        </div>
      )}
      {!ready && (
        <div className={styles.reroll}>
          <div>
            <strong>초기 능력 재평가</strong>
            <p>이전 스탯으로 돌아갈 수 없어.</p>
          </div>
          <button
            disabled={busy || character.rerolls_remaining === 0}
            onClick={reroll}
          >
            ⟳ 능력 재추첨 <b>{character.rerolls_remaining}/10</b>
          </button>
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
