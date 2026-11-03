/* 탐색·인벤토리 데이터와 열린 보조 창을 메인/서브콘솔 사이에서 공유한다. */
"use client";
import {
  createContext,
  createElement,
  useContext,
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useGame } from "./useGame";
import { api } from "../lib/api";
import type {
  ExplorationAction,
  ExplorationState,
  InventoryData,
  WorldMap,
} from "../lib/exploration";

// Exploration state lives in MySQL; panels only suspend input, never reset this hook.
function useExplorationState() {
  const accountGame = useGame();
  const [maps, setMaps] = useState<WorldMap[]>([]);
  const [state, setState] = useState<ExplorationState | null>(null);
  const [inventory, setInventory] = useState<InventoryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const alive = useRef(true);

  const reload = useCallback(async () => {
    const [maps, state, inventory] = await Promise.all([
      api<WorldMap[]>("/maps"),
      api<ExplorationState | null>("/exploration/state"),
      api<InventoryData>("/inventory"),
    ]);
    if (alive.current) {
      setMaps(maps);
      setState(state);
      setInventory(inventory);
    }
  }, []);

  useEffect(() => {
    alive.current = true;
    void reload()
      .catch((error) => {
        if (alive.current) setError((error as Error).message);
      })
      .finally(() => {
        if (alive.current) setLoading(false);
      });
    return () => {
      alive.current = false;
    };
  }, [reload]);

  async function mutate(path: string, body: unknown) {
    if (inFlight.current) return;
    inFlight.current = true;
    setBusy(true);
    setError("");
    try {
      const next = await api<ExplorationState>(path, body);
      if (alive.current) setState(next);
      if (next.dead) {
        await accountGame.reloadAccount();
        return;
      }
      const [inventory, maps] = await Promise.all([
        api<InventoryData>("/inventory"),
        api<WorldMap[]>("/maps"),
      ]);
      if (alive.current) {
        setInventory(inventory);
        setMaps(maps);
      }
    } catch (error) {
      if (alive.current) setError((error as Error).message);
      // On stale version or network failure, reconcile without replaying the action.
      try {
        await reload();
      } catch {
        /* Keep the last confirmed state. */
      }
    } finally {
      inFlight.current = false;
      if (alive.current) setBusy(false);
    }
  }
  function start(mapId: number) {
    return mutate("/exploration/start", { map_id: mapId });
  }
  function act(action: ExplorationAction, itemId?: number) {
    if (!state) return Promise.resolve();
    return mutate("/exploration/action", {
      action,
      ...(itemId === undefined ? {} : { item_id: itemId }),
      exploration_id: state.id,
      version: state.version,
    });
  }
  return { maps, state, inventory, loading, busy, error, start, act, reload };
}

type ConsoleWindow = "inventory" | "encyclopedia" | null;
type SharedExploration = ReturnType<typeof useExplorationState> & {
  window: ConsoleWindow;
  setWindow: (value: ConsoleWindow) => void;
};
const ExplorationContext = createContext<SharedExploration | null>(null);
export function ExplorationProvider({ children }: { children: ReactNode }) {
  const game = useExplorationState();
  const [window, setWindow] = useState<ConsoleWindow>(null);
  return createElement(
    ExplorationContext.Provider,
    { value: { ...game, window, setWindow } },
    children,
  );
}
export function useExploration() {
  const game = useContext(ExplorationContext);
  if (!game) throw new Error("ExplorationProvider가 필요합니다.");
  return game;
}
