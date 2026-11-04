/* 인증·캐릭터 상태를 확인한 뒤 보급 상점을 메인 콘솔에 연다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import Link from "next/link";
import { useGame } from "../../hooks/useGame";
import { AppShell } from "../../components/layout/AppShell";
import { ShopWorkspace } from "../../components/shop/ShopWorkspace";
export default function ShopPage() {
  /* 정상 등록된 캐릭터에게 상점 화면을 제공한다. */
  const game = useGame();
  const character = game.account?.character;
  return (
    <AppShell
      username={game.account?.username}
      ready={character?.status === "ready"}
      auth={game}
    >
      {game.loading ? (
        <p>상점 연결 중…</p>
      ) : character?.status === "ready" ? (
        <ShopWorkspace />
      ) : (
        <section
          className={sharedStyles.panel}
          data-ui="panel"
        >
          <p>물품 거래에는 등록된 피계약자가 필요해.</p>
          <Link href="/character">피계약자 관리로 →</Link>
        </section>
      )}
    </AppShell>
  );
}
