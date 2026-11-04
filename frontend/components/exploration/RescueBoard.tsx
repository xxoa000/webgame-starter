/* 동일 맵의 구조 요청을 조회하고 정상 캐릭터가 지원하도록 한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Exploration.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useExploration } from "../../hooks/useExploration";
type Request = {
  id: number;
  name: string;
  remaining_seconds: number;
};
export function RescueBoard() {
  /* 구조 지원에는 스태미나 1과 한 턴을 사용한다. */
  const game = useExploration();
  const [rows, setRows] = useState<Request[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    /* 활성 맵의 요청을 주기적으로 읽고 페이지를 떠나면 중단한다. */
    let alive = true;
    async function refresh() {
      /* 만료되거나 완료된 구조 요청을 갱신한다. */ try {
        const value = await api<Request[]>("/rescue/nearby");
        if (alive) setRows(value);
      } catch {
        if (alive) setRows([]);
      }
    }
    void refresh();
    const timer = setInterval(() => {
      /* 구조 요청을 10초마다 조회한다. */ if (!document.hidden) void refresh();
    }, 10000);
    return () => {
      /* 후속 요청의 화면 반영을 취소한다. */ alive = false;
      clearInterval(timer);
    };
  }, [game.state?.map_id, game.state?.version]);
  if (!rows.length) return null;
  return (
    <section
      className={classNames(sharedStyles.panel, styles.rescueBoard)}
      data-ui="panel"
    >
      <h3>인근 구조 요청</h3>
      {rows.map((row) => {
        /* 같은 맵의 구조 대상만 표시한다. */ return (
          <div key={row.id}>
            <span>{row.name}</span>
            <button
              disabled={
                busy ||
                game.busy ||
                game.window !== null ||
                !!game.state?.combat ||
                !!game.state?.pending_item ||
                !!game.state?.downed
              }
              onClick={async () => {
                /* 서버가 양쪽 상태와 자원을 검사한 뒤 구조한다. */ setBusy(
                  true,
                );
                setError("");
                try {
                  await api(`/rescue/${row.id}/help`, {});
                  await game.reload();
                  setRows((previous) =>
                    previous.filter((item) => item.id !== row.id),
                  );
                } catch (e) {
                  setError(e instanceof Error ? e.message : "구조 실패");
                } finally {
                  setBusy(false);
                }
              }}
            >
              구조 · 스태미나 -1
            </button>
          </div>
        );
      })}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
