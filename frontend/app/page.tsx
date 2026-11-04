/* 메인콘솔 홈에 균열 경보와 공지를 표시한다. 피계약자 상태는 공통 서브콘솔에 표시한다. */
"use client";

import styles from "../components/home/Home.module.css";
import { useEffect, useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { NoticeBoard } from "../components/home/NoticeBoard";
import { RiftAlert } from "../components/home/RiftAlert";
import { useGame } from "../hooks/useGame";
import { api } from "../lib/api";
import type { RaidEvent } from "../lib/raids";
export default function Home() {
  /* 활성 균열 경보와 공지 목록을 표시한다. */

  const game = useGame();
  const character = game.account?.character;
  const ready = character?.status === "ready";
  const [raid, setRaid] = useState<RaidEvent | null>(null);
  useEffect(() => {
    let alive = true;
    const refresh = () => {
      void api<RaidEvent | null>("/raids/current")
        .then((next) => {
          if (alive) setRaid(next);
        })
        .catch(() => {});
    };
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, []);
  const events =
    raid && raid.status !== "closed"
      ? [
          {
            id: String(raid.id),
            name: "균열 이벤트",
            location: raid.map_name,
            active: true,
            startsAt: "",
            endsAt: null,
            progress:
              raid.status === "boss"
                ? 100 * (1 - raid.boss_hp / raid.boss_max_hp)
                : 0,
            objective:
              raid.status === "boss"
                ? `${raid.boss_name} 출현 · 모든 현장 탐사자 레이드 참가 가능`
                : `균열 결정 회수 ${raid.collected}/${raid.threshold} · 이벤트 물자 발견 확률 1%`,
          },
        ]
      : [];
  return (
    <AppShell username={game.account?.username} ready={ready} auth={game}>
      <div className={styles.homeContent}>
        <RiftAlert events={events} />
        <NoticeBoard />
      </div>
    </AppShell>
  );
}
