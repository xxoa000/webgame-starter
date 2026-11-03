/* 맵별 발견 도감을 작은 격자 칸으로 표시한다. 미발견 이름은 ???로 유지하고 발견 확률을 표시한다. */
"use client";
import { useState } from "react";
import type { WorldMap } from "../../lib/exploration";
export function EncyclopediaPanel({ maps }: { maps: WorldMap[] }) {
  /* 맵별 발견 아이템과 미확인 항목을 표시한다. */

  const [mapId, setMapId] = useState<number | null>(null);
  const selected =
    maps.find((map) => {
      /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
        map.id === mapId
      );
    }) ?? maps[0];
  if (!selected) return <p className="tray-message">도감 자료가 없습니다.</p>;
  return (
    <div className="compact-encyclopedia">
      <div className="tray-summary">
        <label className="catalog-map-label">
          탐색 지역
          <select
            aria-label="도감 지역 선택"
            value={selected.id}
            onChange={(event) => {
              /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setMapId(
                Number(event.target.value),
              );
            }}
          >
            {maps.map((map) => {
              /* 각 항목의 화면 요소를 반환한다. */ return (
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
              /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return item.discovered;
            }).length
          }
          /{selected.items.length} 발견
        </span>
      </div>
      <div
        className="storage-cells catalog-cells"
        aria-label={`${selected.name}의 발견 도감`}
      >
        {selected.items.map((item) => {
          /* 각 항목의 화면 요소를 반환한다. */ return (
            <div
              key={item.item_id}
              className={`storage-cell catalog-cell ${item.discovered ? "known" : "unknown"}`}
              title={`${item.discovered ? item.name : "???"} · ${Math.round(item.probability * 100)}%`}
            >
              <span className="storage-icon" aria-hidden="true">
                {item.discovered ? "❋" : "?"}
              </span>
              <span className="storage-name">
                {item.discovered ? item.name : "???"}
              </span>
              <span className="catalog-chance">
                {Math.round(item.probability * 100)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
