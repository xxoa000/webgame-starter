/* 계정·피계약자·외형·자원 및 등록 요청에 사용하는 공통 타입. */
import type { PersonalityKeyword } from "./personality";
import type { Appearance } from "./appearance";
export type Vitals = {
  condition: "정상" | "부상" | "빈사" | "사망";
  hp_current: number;
  hp_max: number;
  hp_percent: number;
  mp_current: number;
  mp_max: number;
  mp_percent: number;
  stamina_current: number;
  stamina_max: number;
  next_stamina_seconds: number;
  full_stamina_seconds: number;
  server_time: string;
};
export type Character = {
  stat_points: number;
  stat_version: number;
  downed: boolean;
  personality: PersonalityKeyword[];
  name_changes_remaining: number;
  age_changes_remaining: number;
  appearance: Appearance;
  vitals: Vitals | null;
  id: number;
  name: string;
  gender: string;
  age: number | null;
  bio: string;
  stats: Record<string, number>;
  status: "draft" | "ready" | "dead";
  rerolls_used: number;
  rerolls_remaining: number;
};
export type Account = {
  money: number;
  username: string;
  auth: 0 | 1 | 9;
  user_status: 0 | 1 | 2 | 3;
  character: Character | null;
};
export type ProfileInput = {
  personality_keyword_ids: number[];
  appearance: Appearance;
  name: string;
  gender: "male" | "female";
  age: number;
  bio: string;
};
export type StatRanges = Record<string, [number, number]>;
export type RunAction = (operation: () => Promise<void>) => Promise<void>;

export type ProfileUpdate = {
  name?: string;
  age?: number;
  gender?: "male" | "female";
  bio?: string;
};
