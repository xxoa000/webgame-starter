/* 선택한 맵의 물자 목록과 확률을 표시한다. */
import { itemFrame } from "../items/ItemIndicators";
import styles from "./Observation.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import type { WorldMap } from "../../lib/exploration";
export function MapLootPreview({ map }: { map: WorldMap | undefined }) {
  /* 선택한 맵의 물자 목록과 확률을 표시한다. */

  return (
    <section className={styles.mapLootSection}>
      <div className={sharedStyles.smallLabel} data-ui="smallLabel">
        발견할 수 있는 아이템
      </div>
      <div className={styles.itemProbabilities}>
        {map?.items.map((item) => {
          return (
            <span
              key={item.item_id}
              className={itemFrame(item.rarity)}
              title={item.rarity ?? "common"}
            >
              {item.discovered ? item.name : "???"}{" "}
              <b>{Math.round(item.probability * 100)}%</b>
            </span>
          );
        })}
      </div>
    </section>
  );
}
