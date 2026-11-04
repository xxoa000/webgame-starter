/* 탐색 화면이 보이는 동안 접속 신호를 보내 맵별 탐사 인원을 갱신한다. */
"use client";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
type Presence = { counts: Record<string, number>; ttl_seconds: number };
export function useMapPresence(active: boolean, mapId?: number) {
  /* 숨긴 탭은 신호를 중단하고 복귀 시 즉시 갱신한다. */
  const [counts, setCounts] = useState<Record<string, number> | null>(null);
  useEffect(() => {
    /* 상태 전환·맵 변경 후 오래된 응답은 무시한다. */
    let disposed = false;
    let pending = false;
    async function refresh() {
      /* 비활성 창과 중복 요청을 제외하고 서버 집계를 가져온다. */
      if (document.visibilityState !== "visible" || pending) return;
      pending = true;
      try {
        const result = await api<Presence>(
          "/exploration/presence",
          active ? {} : undefined,
        );
        if (!disposed) setCounts(result.counts);
      } catch {
        /* 통신 실패를 실제 0명으로 표시하지 않는다. */
        if (!disposed) setCounts(null);
      } finally {
        pending = false;
      }
    }
    void refresh();
    const timer = setInterval(() => {
      /* 접속 신호를 주기적으로 전송한다. */ void refresh();
    }, 25000);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      /* 타이머와 이벤트를 정리하여 페이지 밖에서는 신호를 보내지 않는다. */
      disposed = true;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [active, mapId]);
  return counts;
}
