/* 전역 계정·피계약자 상태를 공유하고 인증·생성·자원 갱신을 처리한다. */
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
import type { Appearance } from "../lib/appearance";
import { api } from "../lib/api";
import type {
  Vitals,
  Account,
  Character,
  ProfileInput,
  ProfileUpdate,
  StatRanges,
} from "../lib/types";

// Account state and API operations. Components own their local form inputs.
function useGameState() {
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [ranges, setRanges] = useState<StatRanges>({});
  const pending = useRef(false);

  useEffect(() => {
    let active = true;
    api<Account>("/me")
      .then((value) => {
        if (active) setAccount(value);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });
    api<{ ranges: StatRanges }>("/characters/rules")
      .then((value) => {
        if (active) setRanges(value.ranges);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const id = account?.character?.id;
    if (!id || account?.character?.status !== "ready") return;
    let active = true;
    let pending = false;
    const refresh = async () => {
      if (pending || document.hidden) return;
      pending = true;
      try {
        const vitals = await api<Vitals>("/characters/vitals");
        if (active)
          setAccount((previous) =>
            previous?.character?.id === id
              ? { ...previous, character: { ...previous.character, vitals } }
              : previous,
          );
      } catch {
        try {
          const fresh = await api<Account>("/me");
          if (active) setAccount(fresh);
        } catch {}
      } finally {
        pending = false;
      }
    };
    const timer = setInterval(() => void refresh(), 5000);
    document.addEventListener("visibilitychange", refresh);
    return () => {
      active = false;
      clearInterval(timer);
      document.removeEventListener("visibilitychange", refresh);
    };
  }, [account?.character?.id, account?.character?.status]);

  const run = useCallback(async (operation: () => Promise<void>) => {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setNotice("");
    try {
      await operation();
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "요청에 실패했어.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }, []);

  function updateCharacter(character: Character | null) {
    setAccount((previous) =>
      previous ? { ...previous, character } : previous,
    );
  }
  async function login(username: string, password: string) {
    await api("/auth/login", { username, password });
    setAccount(await api<Account>("/me"));
  }
  async function logout() {
    await api("/auth/logout", {});
    setAccount(null);
  }
  async function startCharacter() {
    updateCharacter(await api<Character>("/characters/draft", {}));
  }
  async function reroll() {
    updateCharacter(await api<Character>("/characters/reroll", {}));
  }
  async function finalize(profile: ProfileInput) {
    updateCharacter(await api<Character>("/characters/finalize", profile));
  }
  async function saveAppearance(appearance: Appearance) {
    updateCharacter(
      await api<Character>("/characters/appearance", { appearance }),
    );
    setNotice("피계약자 외형을 저장했어.");
  }
  async function updateProfile(profile: ProfileUpdate): Promise<void> {
    /* 저장 결과로 수정 기회와 프로필을 동기화한다. */
    updateCharacter(
      await api<Character>("/characters/profile", profile, "PATCH"),
    );
    setNotice("인적사항을 저장했어.");
  }
  async function selectPersonality(ids: number[]): Promise<void> {
    /* 기존 캐릭터의 최초 성격 선택을 저장한다. */
    updateCharacter(
      await api<Character>("/characters/personality", {
        personality_keyword_ids: ids,
      }),
    );
  }
  async function deleteCharacter(id: number, name: string) {
    await api("/characters/delete", { character_id: id, name });
    updateCharacter(null);
    setNotice("캐릭터를 삭제했어. 새 캐릭터를 생성할 수 있어.");
  }
  return {
    account,
    reloadAccount: async () => setAccount(await api<Account>("/me")),
    loading,
    busy,
    notice,
    ranges,
    run,
    setNotice,
    login,
    logout,
    startCharacter,
    reroll,
    finalize,
    saveAppearance,
    deleteCharacter,
    updateProfile,
    selectPersonality,
  };
}

const GameContext = createContext<ReturnType<typeof useGameState> | null>(null);
export function GameProvider({ children }: { children: ReactNode }) {
  const game = useGameState();
  return createElement(GameContext.Provider, { value: game }, children);
}
export function useGame() {
  const game = useContext(GameContext);
  if (!game) throw new Error("GameProvider가 필요합니다.");
  return game;
}
