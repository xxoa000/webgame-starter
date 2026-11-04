/* 일반 게시판과 운영 권한에 따른 게시글 관리 화면을 연다. */
"use client";

import { useGame } from "../../hooks/useGame";
import { AppShell } from "../../components/layout/AppShell";
import { PostBoard } from "../../components/posts/PostBoard";
export default function PostsPage() {
  /* 공통 콘솔 안에 게시판을 표시한다. */
  const game = useGame();
  return (
    <AppShell
      username={game.account?.username}
      ready={game.account?.character?.status === "ready"}
      auth={game}
    >
      {game.loading ? <p>불러오는 중…</p> : <PostBoard />}
    </AppShell>
  );
}
