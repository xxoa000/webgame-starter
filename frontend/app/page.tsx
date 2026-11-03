/* 메인콘솔 홈에 균열 경보와 공지를 표시한다. 피계약자 상태는 공통 서브콘솔에 표시한다. */
"use client";
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
    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

    setNow(Date.now());
    const timer = setInterval(() => {
      /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setNow(
        Date.now(),
      );
    }, 1000);
    return () => {
      /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return clearInterval(
        timer,
      );
    };
  }, []);
  const events = now === null ? [] : activeRifts(now);
  return (
    <AppShell username={game.account?.username} ready={ready} auth={game}>
      <div className="home-content">
        <RiftAlert events={events} />
        <NoticeBoard />
      </div>
    </AppShell>
  );
}
