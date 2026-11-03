/* 기본 능력치의 표시 순서와 한국어 이름·성별 표기를 정의한다. */
// Always render in this order, regardless of MySQL JSON key order.
export const STAT_ORDER = [
  "strength",
  "stamina",
  "intelligence",
  "agility",
  "luck",
];
export const CORE_STATS = [
  "strength",
  "stamina",
  "intelligence",
  "agility",
  "luck",
];
export const STAT_LABELS: Record<string, string> = {
  strength: "근력",
  stamina: "체력",
  intelligence: "지능",
  agility: "민첩",
  luck: "행운",
};
export const GENDER_LABELS: Record<string, string> = {
  male: "남자",
  female: "여자",
  other: "성별 선택 필요",
};
