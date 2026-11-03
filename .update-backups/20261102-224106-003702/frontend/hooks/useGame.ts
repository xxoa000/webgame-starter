"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type {
  Account,
  Character,
  ProfileInput,
  StatRanges,
} from "../lib/types";

// Account state and API operations. Components own their local form inputs.
export function useGame() {
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
  async function deleteCharacter(id: number, name: string) {
    await api("/characters/delete", { character_id: id, name });
    updateCharacter(null);
    setNotice("캐릭터를 삭제했어. 새 캐릭터를 생성할 수 있어.");
  }
  return {
    account,
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
    deleteCharacter,
  };
}
