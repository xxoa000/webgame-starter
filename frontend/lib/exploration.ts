/* 맵·인벤토리·탐색과 전투 상태의 API 타입을 정의한다. */
export type InventoryItem = {
  item_id: number;
  name: string;
  description: string;
  usable: boolean;
  kind: string;
  quantity: number;
  weight_grams: number;
  total_weight_grams: number;
};
import type { Vitals } from "./types";
export type WorldMap = {
  monsters: { name: string; probability: number }[];
  id: number;
  name: string;
  description: string;
  empty_probability: number;
  items: {
    item_id: number;
    name: string;
    weight_grams: number | null;
    discovered: boolean;
    probability: number;
  }[];
};
export type InventoryData = {
  character_id: number;
  slot_capacity: number;
  used_slots: number;
  max_weight_grams: number;
  current_weight_grams: number;
  items: InventoryItem[];
};
export type CombatState = {
  monster_id: number;
  name: string;
  description: string;
  hp: number;
  max_hp: number;
};
export type ExplorationState = {
  combat: CombatState | null;
  dead: boolean;
  vitals: Vitals;
  id: number;
  map_id: number;
  map_name: string;
  status: "active" | "ended";
  turn: number;
  version: number;
  pending_item: {
    item_id: number;
    name: string;
    description: string;
    weight_grams: number;
    quantity: number;
  } | null;
  history: {
    turn: number;
    kind: string;
    message: string;
    event_key?: string;
    scripts?: ScriptOutput[];
  }[];
};
export type ExplorationAction =
  | "search"
  | "rest"
  | "take"
  | "give_up"
  | "end"
  | "fight"
  | "flee"
  | "use_item";
export const kilograms = (grams: number) =>
  (grams / 1000).toLocaleString("ko-KR", { maximumFractionDigits: 3 });

export type ScriptOutput = {
  script_id: number;
  version_id: number;
  version: number;
  layer: "SPEECH" | "THOUGHT" | "NARRATION";
  visibility: "PUBLIC" | "OWNER";
  content: string;
};
