/* 메인 화면 하단 20%에 인벤토리·도감을 도킹한다. 위쪽 작업 영역은 독립적으로 스크롤한다. */
"use client";
import type { ReactNode } from "react";
import { useExploration } from "../../hooks/useExploration";
import { InventoryPanel } from "../inventory/InventoryPanel";
import { EncyclopediaPanel } from "../exploration/EncyclopediaPanel";
function ConnectedMain({ children }: { children: ReactNode }) {
  /* 화면 상태를 확인하고 ConnectedMain 기능을 실행한다. */

  const game = useExploration();
  return (
    <div className={`main-screen-layout ${game.window ? "tray-open" : ""}`}>
      <div className="main-workspace">{children}</div>
      {game.window && (
        <section
          className="equipment-tray"
          aria-label={game.window === "inventory" ? "인벤토리" : "도감"}
        >
          <div className="equipment-tray-header">
            <div className="tray-tabs">
              <button
                aria-pressed={game.window === "inventory"}
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return game.setWindow(
                    "inventory",
                  );
                }}
              >
                인벤토리
              </button>
              <button
                aria-pressed={game.window === "encyclopedia"}
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return game.setWindow(
                    "encyclopedia",
                  );
                }}
              >
                도감
              </button>
            </div>
            <button
              className="tray-close"
              aria-label="하단 패널 닫기"
              onClick={() => {
                /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return game.setWindow(
                  null,
                );
              }}
            >
              닫기 ×
            </button>
          </div>
          <div className="equipment-tray-body">
            {game.window === "inventory" ? (
              <InventoryPanel inventory={game.inventory} />
            ) : (
              <EncyclopediaPanel maps={game.maps} />
            )}
          </div>
        </section>
      )}
    </div>
  );
}
export function MainConsole({
  ready,
  children,
}: {
  ready: boolean;
  children: ReactNode;
}) {
  /* 메인 작업 공간과 하단 보조 창을 배치한다. */

  return ready ? (
    <ConnectedMain>{children}</ConnectedMain>
  ) : (
    <div className="main-screen-layout">
      <div className="main-workspace">{children}</div>
    </div>
  );
}
