export type Character = {
  id: number;
  name: string;
  gender: string;
  age: number | null;
  bio: string;
  stats: Record<string, number>;
  status: "draft" | "ready";
  rerolls_used: number;
  rerolls_remaining: number;
};
export type Account = { username: string; character: Character | null };
export type ProfileInput = {
  name: string;
  gender: string;
  age: number;
  bio: string;
};
export type StatRanges = Record<string, [number, number]>;
export type RunAction = (operation: () => Promise<void>) => Promise<void>;
