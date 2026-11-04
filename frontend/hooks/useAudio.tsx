/* 페이지 이동에도 유지되는 오디오 설정과 사용자 동작 기반 재생을 제공한다. */
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { usePathname } from "next/navigation";
import {
  AUDIO_STORAGE_KEY,
  DEFAULT_AUDIO,
  GameAudio,
  volume,
  type AudioSettings,
  type SoundEffect,
} from "../lib/audio";
import { AudioSettingsButton } from "../components/audio/AudioSettingsButton";

type AudioControls = {
  settings: AudioSettings;
  setVolume: (channel: keyof AudioSettings, value: number) => void;
  play: (effect: SoundEffect, delay?: number) => void;
  ready: boolean;
  error: boolean;
};
const AudioContext = createContext<AudioControls | null>(null);

export function AudioProvider({ children }: { children: ReactNode }) {
  /* 인증·탐색 상태와 무관하게 하나의 오디오 엔진을 유지한다. */
  const engine = useRef<GameAudio | null>(null);
  const [settings, setSettings] = useState(DEFAULT_AUDIO);
  const [hydrated, setHydrated] = useState(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    let alive = true;
    const audio = new GameAudio(() => {
      if (alive) setError(true);
    });
    engine.current = audio;
    try {
      const stored = JSON.parse(
        localStorage.getItem(AUDIO_STORAGE_KEY) ?? "null",
      );
      if (stored && typeof stored === "object") {
        setSettings({
          music: volume(stored.music, DEFAULT_AUDIO.music),
          effects: volume(stored.effects, DEFAULT_AUDIO.effects),
        });
      }
    } catch {
      /* 저장소 접근이 제한되어도 현재 탭에서는 설정할 수 있다. */
    }
    setHydrated(true);
    const unlock = () => {
      void audio
        .unlock()
        .then((active) => {
          if (alive) setReady(active);
        })
        .catch(() => {
          if (alive) setError(true);
        });
    };
    const click = (event: MouseEvent) => {
      if (!event.isTrusted || !(event.target instanceof Element)) return;
      const target = event.target.closest(
        "button, a[href], input[type=button], input[type=submit], [role=button]",
      );
      if (!target || target.closest('[disabled], [aria-disabled="true"]'))
        return;
      void audio
        .unlock()
        .then(() => audio.play("click"))
        .catch(() => {
          if (alive) setError(true);
        });
    };
    const visibility = () => audio.visibility(document.hidden);
    document.addEventListener("pointerdown", unlock, { passive: true });
    document.addEventListener("keydown", unlock);
    document.addEventListener("click", click, true);
    document.addEventListener("visibilitychange", visibility);
    return () => {
      alive = false;
      document.removeEventListener("pointerdown", unlock);
      document.removeEventListener("keydown", unlock);
      document.removeEventListener("click", click, true);
      document.removeEventListener("visibilitychange", visibility);
      audio.dispose();
      engine.current = null;
    };
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    engine.current?.setVolumes(settings);
    try {
      localStorage.setItem(AUDIO_STORAGE_KEY, JSON.stringify(settings));
    } catch {
      /* 개인정보 보호 모드에서는 현재 탭의 값만 유지한다. */
    }
  }, [settings, hydrated]);

  useEffect(() => {
    engine.current?.setScene(
      pathname.startsWith("/explore") ? "exploration" : "control-room",
    );
  }, [pathname]);

  const play = useCallback((effect: SoundEffect, delay = 0) => {
    void engine.current?.play(effect, delay);
  }, []);
  const setVolume = useCallback(
    (channel: keyof AudioSettings, value: number) => {
      setSettings((previous) => ({
        ...previous,
        [channel]: volume(value, previous[channel]),
      }));
    },
    [],
  );
  return (
    <AudioContext.Provider value={{ settings, setVolume, play, ready, error }}>
      {children}
      <AudioSettingsButton />
    </AudioContext.Provider>
  );
}

export function useAudio() {
  /* 효과음 호출부는 설정과 재생 정책을 직접 관리하지 않는다. */
  const audio = useContext(AudioContext);
  if (!audio) throw new Error("AudioProvider가 필요합니다.");
  return audio;
}
