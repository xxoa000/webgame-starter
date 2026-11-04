/* 서브 콘솔 프로필 아래에 인벤토리·도감과 무게·재화를 표시한다. */
"use client";

import type { ReactNode } from "react";
import styles from "./Console.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import { usePathname } from "next/navigation";
import { useExploration } from "../../hooks/useExploration";
import { useGame } from "../../hooks/useGame";
import { InventoryPanel } from "../inventory/InventoryPanel";
import { EncyclopediaPanel } from "../exploration/EncyclopediaPanel";
import { kilograms } from "../../lib/exploration";
export function SubEquipment({ children }: { children?: ReactNode }) {
  /* 상점에서는 인벤토리를 고정하고 다른 페이지에서는 버튼으로 전환한다. */
  const game = useExploration();
  const account = useGame();
  const shop = usePathname().startsWith("/shop");
  const opened = game.window;
  return (
    <section className={styles.subEquipment}>
      <div className={styles.subEquipmentToolbar}>
        <div className={styles.subEquipmentTabs}>
          <button
            aria-label="인벤토리"
            title="인벤토리"
            aria-expanded={opened === "inventory"}
            onClick={() => {
              /* 소지품 창을 전환한다. */
              game.setWindow(opened === "inventory" ? null : "inventory");
            }}
          >
            <svg
              viewBox="0 0 16 16"
              aria-hidden="true"
              shapeRendering="crispEdges"
            >
              <path
                fill="currentColor"
                d="M5 1h6v2h2v2h1v9H2V5h1V3h2V1zm1 2v2h4V3H6zM4 7v2h8V7H4zm1 4v2h6v-2H5z"
              />
            </svg>
          </button>

          <button
            aria-label="도감"
            title="도감"
            disabled={shop}
            aria-expanded={opened === "encyclopedia"}
            onClick={() => {
              /* 도감 창을 전환한다. */
              game.setWindow(opened === "encyclopedia" ? null : "encyclopedia");
            }}
          >
            <svg
              viewBox="0 0 16 16"
              aria-hidden="true"
              shapeRendering="crispEdges"
            >
              <path
                fill="currentColor"
                d="M1 2h5v1h4V2h5v11h-5v1H6v-1H1V2zm2 2v7h3v1h1V5H6V4H3zm6 1v7h1v-1h3V4h-3v1H9z"
              />
            </svg>
          </button>
        </div>

        <div className={styles.subCargoSummary}>
          <span>
            {kilograms(game.inventory?.current_weight_grams ?? 0)} /
            {kilograms(game.inventory?.max_weight_grams ?? 30000)} kg
          </span>
          <span>
            {(
              game.inventory?.money ??
              account.account?.money ??
              0
            ).toLocaleString()}{" "}
            C
          </span>
        </div>
      </div>
      {children}

      {opened && (
        <div className={styles.subEquipmentBody} data-ui="subEquipmentBody">
          <div className={styles.equipmentHeading}>
            <strong>
              {opened === "inventory"
                ? `인벤토리 · ${game.inventory?.used_slots ?? 0}/${game.inventory?.slot_capacity ?? 10}칸`
                : "도감"}
            </strong>
            <button
              type="button"
              aria-label="보조 창 닫기"
              onClick={() => game.setWindow(null)}
            >
              ×
            </button>
          </div>
          {opened === "inventory" ? (
            <InventoryPanel inventory={game.inventory} />
          ) : (
            <EncyclopediaPanel maps={game.maps} />
          )}
        </div>
      )}

      {game.error && (
        <p className={sharedStyles.helpText} role="alert" data-ui="helpText">
          {game.error}
        </p>
      )}
    </section>
  );
}
