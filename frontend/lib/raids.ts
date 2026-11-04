/* 서버가 관리하는 공유 균열의 진행·기여·정산 응답이다. */
export type RaidEvent = {
  id: number;
  map_id: number;
  map_name: string;
  status: "collecting" | "boss" | "closed";
  collected: number;
  threshold: number;
  boss_name: string;
  boss_hp: number;
  boss_max_hp: number;
  version: number;
  my_items: number;
  my_reward: number;
  leaders: { name: string; damage: number; reward: number }[];
  closed_at: string | null;
};
