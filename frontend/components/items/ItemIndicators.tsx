/* 아이템 등급 테두리·태그와 섭취 가능한 식음료의 도트 고기 표시를 제공한다. */
import styles from "./Items.module.css";
import type { ItemTraits, Rarity } from "../../lib/items";
const grades: Record<Rarity, string> = {
  common: styles.common,
  uncommon: styles.uncommon,
  rare: styles.rare,
  epic: styles.epic,
  legendary: styles.legendary,
  mythic: styles.mythic,
};
export function itemFrame(rarity?: Rarity) {
  /* API에 등급이 없는 이전 데이터는 기본 common으로 표시한다. */
  return `${styles.frame} ${grades[rarity ?? "common"] ?? styles.common}`;
}
export function ItemIndicators({
  rarity = "common",
  edible = false,
}: ItemTraits) {
  /* 기존 이미지 영역 위에 표시하며 칸의 크기나 여백은 바꾸지 않는다. */
  return (
    <>
      <span className={styles.rarityTag}>{rarity}</span>
      {edible && (
        <span
          className={styles.edibleMark}
          role="img"
          aria-label="섭취 가능"
          title="섭취 가능"
        >
          <svg
            viewBox="0 0 16 16"
            shapeRendering="crispEdges"
            aria-hidden="true"
          >
            <path fill="#ead9b9" d="M1 11h3v3H1zM3 10h3v3H3z" />
            <path
              fill="#b46d58"
              d="M5 3h3V2h4v1h2v2h1v5h-2v2H9v1H6v-2H4V6h1z"
            />
            <path fill="#e5ad83" d="M8 4h4v1h1v4h-2v2H8V9H6V6h2z" />
            <path fill="#e9d4b3" d="M9 6h2v2H9z" />
          </svg>
        </span>
      )}
    </>
  );
}
