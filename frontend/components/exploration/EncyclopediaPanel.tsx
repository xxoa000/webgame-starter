/* 맵별 발견 도감을 작은 격자 칸으로 표시한다. 미발견 이름은 ???로 유지하고 발견 확률을 표시한다. */
"use client";

import { ItemIndicators, itemFrame } from "../items/ItemIndicators";
import styles from "./Exploration.module.css";
import { classNames } from "../../lib/classNames";
import { useState } from "react";
import type { WorldMap } from "../../lib/exploration";
export function EncyclopediaPanel({ maps }: { maps: WorldMap[] }) {
  /* 맵별 발견 아이템과 미확인 항목을 표시한다. */

  const [mapId, setMapId] = useState<number | null>(null);
  const selected =
    maps.find((map) => {
      return map.id === mapId;
    }) ?? maps[0];
  if (!selected)
    return <p className={styles.trayMessage}>도감 자료가 없습니다.</p>;
  return (
    <div className={styles.compactEncyclopedia}>
      <div className={styles.traySummary}>
        <label className={styles.catalogMapLabel}>
          탐색 지역
          <select
            aria-label="도감 지역 선택"
            value={selected.id}
            onChange={(event) => {
              return setMapId(Number(event.target.value));
            }}
          >
            {maps.map((map) => {
              return (
                <option key={map.id} value={map.id}>
                  {map.name}
                </option>
              );
            })}
          </select>
        </label>
        <span>
          {
            selected.items.filter((item) => {
              return item.discovered;
            }).length
          }
          /{selected.items.length} 발견
        </span>
      </div>
      <div
        className={styles.storageCells}
        aria-label={`${selected.name}의 발견 도감`}
      >
        {selected.items.map((item) => {
          return (
            <div
              key={item.item_id}
              className={classNames(
                styles.itemSlot,
                itemFrame(item.rarity),
                styles.catalogSlot,
                item.discovered ? "" : styles.unknown,
              )}
              title={`${item.discovered ? item.name : "???"} · ${Math.round(item.probability * 100)}%`}
              data-ui={item.discovered ? "" : ""}
            >
              <ItemIndicators
                rarity={item.rarity}
                edible={item.discovered && item.edible}
              />
              <span className={styles.storageIcon} aria-hidden="true">
                {item.discovered ? "❋" : "?"}
              </span>
              <span className={styles.storageName}>
                {item.discovered ? item.name : "???"}
              </span>
              <span className={styles.catalogChance}>
                {Math.round(item.probability * 100)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
