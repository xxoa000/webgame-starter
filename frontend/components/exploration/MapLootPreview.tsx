/* 선택한 맵의 물자 목록과 확률을 표시한다. */
import type { WorldMap } from "../../lib/exploration";
export function MapLootPreview({ map }: { map: WorldMap | undefined }) {
  /* 선택한 맵의 물자 목록과 확률을 표시한다. */

  return (
    <section className="map-loot-section">
      <div className="mini">발견할 수 있는 아이템</div>
      <div className="map-loot-preview">
        {map?.items.map((item) => {
          /* 각 항목의 화면 요소를 반환한다. */ return (
            <span key={item.item_id}>
              {item.discovered ? item.name : "???"}{" "}
              <b>{Math.round(item.probability * 100)}%</b>
            </span>
          );
        })}
      </div>
    </section>
  );
}
