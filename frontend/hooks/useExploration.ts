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
import { usePathname } from "next/navigation";
import styles from "../components/console/Console.module.css";
import { useGame } from "./useGame";
import { api } from "../lib/api";
import type { RaidEvent } from "../lib/raids";
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
  const [raid, setRaid] = useState<RaidEvent | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const inFlight = useRef(false);
  const alive = useRef(true);
  const reloadVersion = useRef(0);
  const previousRaid = useRef<string | null>(null);

  useEffect(() => {
    /* 다른 탐사자가 끝낸 레이드 보상도 캐릭터 창에 반영한다. */
    const key = raid ? `${raid.id}:${raid.status}` : null;
    if (raid?.status === "closed" && previousRaid.current !== key) {
      void accountGame.reloadAccount().catch(() => {});
    }
    previousRaid.current = key;
  }, [raid?.id, raid?.status]);

  const reload = useCallback(async () => {
    const version = ++reloadVersion.current;
    const raid = await api<RaidEvent | null>("/raids/mine");
    const [maps, state, inventory] = await Promise.all([
      api<WorldMap[]>("/maps"),
      api<ExplorationState | null>("/exploration/state"),
      api<InventoryData>("/inventory").catch((error: unknown) => {
        /* 사망 기록 조회에서만 인벤토리 부재를 허용한다. */
        if (accountGame.account?.character?.status === "dead") return null;
        throw error;
      }),
    ]);
    if (alive.current && version === reloadVersion.current) {
      setMaps(maps);
      setState(state);
      setInventory(inventory);
      setRaid(raid);
    }
  }, [accountGame.account?.character?.status]);

  useEffect(() => {
    /* 공유 보스 HP와 다른 탐사자의 수집 결과를 주기적으로 동기화한다. */
    const timer = setInterval(() => {
      if (!document.hidden && !inFlight.current) {
        void reload().catch(() => {});
      }
    }, 3000);
    return () => clearInterval(timer);
  }, [reload]);

  async function attackRaid() {
    /* 서버 버전으로 중복 공격을 막고 정산 뒤 캐릭터 포인트를 갱신한다. */
    if (!raid || inFlight.current) return;
    inFlight.current = true;
    reloadVersion.current += 1;
    setBusy(true);
    setError("");
    try {
      const next = await api<RaidEvent>(`/raids/${raid.id}/attack`, {
        version: raid.version,
      });
      setRaid(next);
      await reload();
      await accountGame.reloadAccount();
    } catch (error) {
      setError(error instanceof Error ? error.message : "레이드 공격 실패");
      await reload().catch(() => {});
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }

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
    reloadVersion.current += 1;
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
        api<InventoryData>("/inventory").catch((error: unknown) => {
          /* 사망 기록 조회에서만 인벤토리 부재를 허용한다. */
          if (accountGame.account?.character?.status === "dead") return null;
          throw error;
        }),
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
  async function leaveExploration() {
    /* 진행 중 요청이 끝난 뒤 최신 버전으로 확정 도망·종료를 순서대로 처리한다. */
    if (inFlight.current) return false;
    inFlight.current = true;
    reloadVersion.current += 1;
    setBusy(true);
    try {
      let current = await api<ExplorationState | null>("/exploration/state");
      if (!current || current.status !== "active") return true;
      // 빈사 상태는 이동으로 해제하지 않는다. 구조 요청/포기 규칙을 보존한다.
      if (current.downed) return true;
      if (current.combat) {
        current = await api<ExplorationState>("/exploration/action", {
          action: "flee",
          exploration_id: current.id,
          version: current.version,
        });
      }
      const ended = await api<ExplorationState>("/exploration/action", {
        action: "end",
        exploration_id: current.id,
        version: current.version,
      });
      if (alive.current) setState(ended);
      await reload();
      return true;
    } catch (error) {
      setError(error instanceof Error ? error.message : "탐색 종료 실패");
      return true;
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
  async function inventoryAction(
    action: "use" | "discard",
    itemId: number,
    quantity = 1,
  ) {
    /* 소지품 변경 후 계정·자원·탐색 기록을 함께 새로 읽는다. */
    if (inFlight.current) return;
    inFlight.current = true;
    reloadVersion.current += 1;
    setBusy(true);
    setError("");
    try {
      await api<InventoryData>(`/inventory/${action}`, {
        item_id: itemId,
        quantity,
      });
      await reload();
      await accountGame.reloadAccount();
    } catch (error) {
      setError(error instanceof Error ? error.message : "물품 처리 실패");
    } finally {
      inFlight.current = false;
      setBusy(false);
    }
  }
  function rescueAction(action: "request" | "abandon") {
    /* 빈사 상태의 구조 요청·포기를 서버에서 처리한다. */
    return mutate(`/rescue/${action}`, {});
  }
  useEffect(() => {
    /* 구조 대기 중에도 서버 기한과 구조 결과를 계속 확인한다. */
    if (!state?.downed) return;
    const timer = setInterval(() => {
      /* NPC·플레이어 구조로 바뀐 상태를 동기화한다. */
      if (!document.hidden)
        void reload()
          .then(() => accountGame.reloadAccount())
          .catch(() => {});
    }, 5000);
    return () => {
      /* 구조 상태 확인 타이머를 정리한다. */ clearInterval(timer);
    };
  }, [state?.downed, reload]);
  return {
    raid,
    attackRaid,
    maps,
    state,
    inventory,
    clearError: () => setError(""),
    loading,
    busy,
    error,
    start,
    act,
    reload,
    inventoryAction,
    rescueAction,
    leaveExploration,
  };
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
  const pathname = usePathname();
  const previousPath = useRef(pathname);
  const pendingExit = useRef(false);
  const exiting = useRef(false);
  const [transitionMessage, setTransitionMessage] = useState("");
  useEffect(() => {
    /* 페이지별 보조 창은 초기화하고 상점에 들어갈 때만 인벤토리를 연다. */
    const previous = previousPath.current;
    previousPath.current = pathname;
    game.clearError();
    setWindow(pathname.startsWith("/shop") ? "inventory" : null);
    if (previous.startsWith("/explore") && !pathname.startsWith("/explore")) {
      pendingExit.current = true;
      setTransitionMessage(
        game.state?.downed
          ? "구조 대기 상태를 유지합니다."
          : "탐색을 종료합니다.",
      );
    } else if (previous.startsWith("/shop") && !pathname.startsWith("/shop")) {
      setTransitionMessage("상점 이용을 종료합니다.");
    }
    if (pathname.startsWith("/explore")) pendingExit.current = false;
  }, [pathname]);
  useEffect(() => {
    /* 클릭 중 이동한 경우에도 해당 요청 뒤에 종료를 한 번만 실행한다. */
    if (!pendingExit.current || game.busy || exiting.current) return;
    exiting.current = true;
    void game
      .leaveExploration()
      .then((completed) => {
        if (completed) pendingExit.current = false;
      })
      .finally(() => {
        exiting.current = false;
      });
  }, [pathname, game.busy]);
  useEffect(() => {
    /* 짧은 이동 안내만 자동으로 지운다. */
    if (!transitionMessage) return;
    const timer = setTimeout(() => setTransitionMessage(""), 900);
    return () => clearTimeout(timer);
  }, [transitionMessage, pathname]);
  return createElement(
    ExplorationContext.Provider,
    { value: { ...game, window, setWindow } },
    children,
    transitionMessage
      ? createElement(
          "div",
          {
            role: "status",
            className: styles.routeToast,
          },
          transitionMessage,
        )
      : null,
    game.error && !pathname.startsWith("/explore")
      ? createElement(
          "div",
          {
            role: "alert",
            className: styles.routeToast,
          },
          game.error,
        )
      : null,
  );
}
export function useExploration() {
  const game = useContext(ExplorationContext);
  if (!game) throw new Error("ExplorationProvider가 필요합니다.");
  return game;
}
