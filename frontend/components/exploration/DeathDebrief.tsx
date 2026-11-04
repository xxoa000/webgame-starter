/* 사망 직후 마지막 전투·구조 경위를 확인한 뒤 등록 화면으로 이동한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Exploration.module.css";
import { classNames } from "../../lib/classNames";
import Link from "next/link";
import { useExploration } from "../../hooks/useExploration";
export function DeathDebrief() {
  /* 자동 이동 없이 사용자가 사망 경위를 읽고 다음 화면을 선택한다. */
  const game = useExploration();
  return (
    <section
      className={classNames(sharedStyles.panel, styles.deathDebrief)}
      data-ui="panel"
    >
      <div
        className={sharedStyles.smallLabel}
        data-ui="smallLabel"
      >
        FINAL FIELD REPORT
      </div>
      <h2>피계약자 생체 신호 종료</h2>
      <ol>
        {game.state?.history.slice(-8).map((event, index) => {
          /* 마지막 공격과 구조 포기 경위를 시간순으로 표시한다. */ return (
            <li key={event.event_key ?? index}>{event.message}</li>
          );
        })}
      </ol>
      <Link
        className={styles.exploreHomeLink}
        href="/character"
      >
        사망 경위 확인 · 피계약자 관리로 →
      </Link>
    </section>
  );
}
