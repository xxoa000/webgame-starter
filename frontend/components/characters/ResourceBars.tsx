/* HP·MP·스태미나와 부상 상태 및 자연 회복 시간을 표시한다. */
"use client";
import { useEffect, useState } from "react";
import type { Vitals } from "../../lib/types";

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
    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

    setElapsed(0);
    const received = Date.now();
    const timer = setInterval(() => {
      /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setElapsed(
        (Date.now() - received) / 1000,
      );
    }, 1000);
    return () => {
      /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return clearInterval(
        timer,
      );
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
    <div className={`resource-bars ${compact ? "compact" : ""}`}>
      {vitals.condition !== "정상" && vitals.condition && (
        <strong className="condition-injury">{vitals.condition}</strong>
      )}
      {resources.map((resource) => {
        /* 각 항목의 화면 요소를 반환한다. */ return (
          <div
            className={`resource resource-${resource.key}`}
            key={resource.key}
          >
            <div className="resource-label">
              <span>{resource.name}</span>
              <strong>
                {resource.current} / {resource.max}
                {resource.percent !== null ? ` (${resource.percent}%)` : ""}
              </strong>
            </div>
            <div
              className="resource-track"
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
              <small className="recovery-time">
                {resource.current >= resource.max ? (
                  "스태미나 최대치 도달"
                ) : (
                  <>
                    <span>
                      다음 회복까지{" "}
                      {duration(vitals.next_stamina_seconds - elapsed)}
                    </span>
                    <span>
                      완전 회복까지{" "}
                      {duration(vitals.full_stamina_seconds - elapsed)}
                    </span>
                  </>
                )}
              </small>
            )}
          </div>
        );
      })}
    </div>
  );
}
