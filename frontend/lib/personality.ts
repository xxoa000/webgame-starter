/* 성격 분류·키워드와 최초 선택 요청 타입을 정의한다. */
export type PersonalityCategory = "OUTER" | "INNER" | "ALIGNMENT";
export type PersonalityKeyword = {
  id: number;
  category: PersonalityCategory;
  code: string;
  name: string;
  description?: string;
};
export const PERSONALITY_LABELS: Record<PersonalityCategory, string> = {
  OUTER: "겉성격",
  INNER: "속성격",
  ALIGNMENT: "성향",
};
export const PERSONALITY_CATEGORIES: PersonalityCategory[] = [
  "OUTER",
  "INNER",
  "ALIGNMENT",
];
