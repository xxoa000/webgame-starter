export type WorldMap = {
  id: number;
  name: string;
  description: string;
  empty_probability: number;
  items: {
    item_id: number;
    name: string;
    weight_grams: number;
    probability: number;
  }[];
};
export type InventoryData = {
  character_id: number;
  slot_capacity: number;
  used_slots: number;
  max_weight_grams: number;
  current_weight_grams: number;
  items: {
    item_id: number;
    name: string;
    description: string;
    kind: string;
    quantity: number;
    weight_grams: number;
    total_weight_grams: number;
  }[];
};
export type ExplorationState = {
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
  history: { turn: number; kind: string; message: string }[];
};
export type ExplorationAction = "search" | "rest" | "take" | "give_up" | "end";
export const kilograms = (grams: number) =>
  (grams / 1000).toLocaleString("ko-KR", { maximumFractionDigits: 3 });
