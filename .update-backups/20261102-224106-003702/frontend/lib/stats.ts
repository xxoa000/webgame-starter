// Always render in this order, regardless of MySQL JSON key order.
export const STAT_ORDER = [
  "appearance",
  "height_cm",
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
  appearance: "외모",
  height_cm: "키",
  strength: "근력",
  stamina: "체력",
  intelligence: "지능",
  agility: "민첩",
  luck: "행운",
};
export const GENDER_LABELS: Record<string, string> = {
  male: "남성",
  female: "여성",
  other: "기타",
};
