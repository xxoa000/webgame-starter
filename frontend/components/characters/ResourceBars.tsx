/* HP·MP·스태미나와 부상 상태 및 자연 회복 시간을 표시한다. */
"use client";

import styles from "./Characters.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useState } from "react";
import type { Vitals } from "../../lib/types";
const resourceStyles: Record<string, string> = {
  hp: styles.healthBar,
  mp: styles.manaBar,
  stamina: styles.staminaBar,
};
function duration(seconds: number) {
  /* 남은 초를 분과 초로 변환한다. */

  const value = Math.max(0, Math.ceil(seconds));
  return `${Math.floor(value / 60)}분 ${value % 60}초`;
}
export function ResourceBars({
  vitals,
  compact = false,
}: {
  vitals: Vitals | null;
  compact?: boolean;
}) {
  /* 현재 자원과 자연 회복 남은 시간을 표시한다. */

  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    setElapsed(0);
    const received = Date.now();
    const timer = setInterval(() => {
      return setElapsed((Date.now() - received) / 1000);
    }, 1000);
    return () => {
      return clearInterval(timer);
    };
  }, [vitals?.server_time]);
  if (!vitals) return null;
  const resources = [
    {
      key: "hp",
      name: "HP",
      current: vitals.hp_current,
      max: vitals.hp_max,
      percent: vitals.hp_percent,
    },
    {
      key: "mp",
      name: "MP",
      current: vitals.mp_current,
      max: vitals.mp_max,
      percent: vitals.mp_percent,
    },
    {
      key: "stamina",
      name: "스태미나",
      current: vitals.stamina_current,
      max: vitals.stamina_max,
      percent: null,
    },
  ];
  return (
    <div
      className={classNames(styles.resourceBars, compact ? styles.compact : "")}
      data-ui={compact ? "" : ""}
    >
      {vitals.condition !== "정상" && vitals.condition && (
        <strong className={styles.conditionInjury}>{vitals.condition}</strong>
      )}
      {resources.map((resource) => {
        return (
          <div
            className={resourceStyles[resource.key]}
            key={resource.key}
          >
            <div className={styles.resourceLabel}>
              <span>{resource.name}</span>
              <strong>
                {resource.current} / {resource.max}
                {resource.percent !== null ? ` (${resource.percent}%)` : ""}
              </strong>
            </div>
            <div
              className={styles.resourceTrack}
              role="progressbar"
              aria-label={resource.name}
              aria-valuemin={0}
              aria-valuemax={resource.max}
              aria-valuenow={resource.current}
            >
              <span
                style={{
                  width: `${Math.max(0, Math.min(100, (resource.current / resource.max) * 100))}%`,
                }}
              />
            </div>
            {resource.key === "stamina" && (
              <small
                className={styles.recoveryTime}
                title="다음 스태미나 회복까지 / 완전 회복까지"
              >
                {resource.current >= resource.max
                  ? "스태미나 최대치 도달"
                  : `(${duration(vitals.next_stamina_seconds - elapsed)}/${duration(vitals.full_stamina_seconds - elapsed)})`}
              </small>
            )}
          </div>
        );
      })}
    </div>
  );
}
