"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type {
  ExplorationAction,
  ExplorationState,
  InventoryData,
  WorldMap,
} from "../lib/exploration";

// Exploration state lives in MySQL; panels only suspend input, never reset this hook.
export function useExploration() {
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
      const inventory = await api<InventoryData>("/inventory");
      if (alive.current) setInventory(inventory);
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
  function act(action: ExplorationAction) {
    if (!state) return Promise.resolve();
    return mutate("/exploration/action", {
      action,
      exploration_id: state.id,
      version: state.version,
    });
  }
  return { maps, state, inventory, loading, busy, error, start, act, reload };
}
