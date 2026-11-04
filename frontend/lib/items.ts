/* 서버가 계산한 등급과 섭취 여부를 모든 아이템 표시에서 공유한다. */
export type Rarity =
  "common" | "uncommon" | "rare" | "epic" | "legendary" | "mythic";
export type ItemTraits = { rarity?: Rarity; edible?: boolean };
