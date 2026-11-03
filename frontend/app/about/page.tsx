/* 기관 소개 전용 페이지. 네 부서의 역할과 편제를 표시한다. */
"use client";
import { AppShell } from "../../components/layout/AppShell";
import { DepartmentDirectory } from "../../components/world/DepartmentDirectory";
import { useGame } from "../../hooks/useGame";
export default function AboutPage() {
  /* 화면 상태를 확인하고 AboutPage 기능을 실행한다. */

  const game = useGame();
  return (
    <AppShell
      username={game.account?.username}
      ready={game.account?.character?.status === "ready"}
      auth={game}
    >
      <DepartmentDirectory />
    </AppShell>
  );
}
