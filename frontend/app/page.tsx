/* 메인콘솔 홈에 균열 경보와 공지를 표시한다. 피계약자 상태는 공통 서브콘솔에 표시한다. */
"use client";

import styles from "../components/home/Home.module.css";
import { useEffect, useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { NoticeBoard } from "../components/home/NoticeBoard";
import { RiftAlert } from "../components/home/RiftAlert";
import { useGame } from "../hooks/useGame";
import { activeRifts } from "../lib/control";
export default function Home() {
  /* 활성 균열 경보와 공지 목록을 표시한다. */

  const game = useGame();
  const character = game.account?.character;
  const ready = character?.status === "ready";
  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    setNow(Date.now());
    const timer = setInterval(() => {
      return setNow(Date.now());
    }, 1000);
    return () => {
      return clearInterval(timer);
    };
  }, []);
  const events = now === null ? [] : activeRifts(now);
  return (
    <AppShell
      username={game.account?.username}
      ready={ready}
      auth={game}
    >
      <div className={styles.homeContent}>
        <RiftAlert events={events} />
        <NoticeBoard />
      </div>
    </AppShell>
  );
}
