/* 빈사 상태에서 구조 요청·대기·포기를 표시한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Exploration.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useState } from "react";
import { useExploration } from "../../hooks/useExploration";
export function RescuePanel() {
  /* NPC 도착 남은 시간을 표시하며 실제 완료는 서버가 판정한다. */
  const game = useExploration();
  const rescue = game.state?.rescue;
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    /* 화면의 남은 초만 갱신한다. */
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  const seconds = rescue
    ? Math.max(0, Math.ceil((Date.parse(rescue.due_at) - now) / 1000))
    : 0;
  return (
    <section
      className={classNames(sharedStyles.panel, styles.rescuePanel)}
      data-ui="panel"
    >
      <div
        className={sharedStyles.smallLabel}
        data-ui="smallLabel"
      >
        CRITICAL / HP 1
      </div>
      <h2>빈사 상태</h2>
      <p>치명상으로 전투가 종료됐다. 이동과 아이템 사용이 불가능하다.</p>
      {rescue?.status === "waiting" ? (
        <p role="status">구조 요청 송신 완료 · 치료 NPC 도착까지 {seconds}초</p>
      ) : (
        <button
          disabled={game.busy}
          onClick={() => {
            /* 구조 요청을 한 번만 등록한다. */
            void game.rescueAction("request");
          }}
        >
          구조 요청
        </button>
      )}

      <button
        disabled={game.busy}
        onClick={() => {
          /* 구조 포기는 확인 후 사망을 확정한다. */
          if (globalThis.confirm("구조를 포기하고 피계약자의 사망을 확정할까?"))
            void game.rescueAction("abandon");
        }}
      >
        구조 포기
      </button>
    </section>
  );
}
