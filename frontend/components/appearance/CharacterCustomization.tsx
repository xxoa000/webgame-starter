/* 성별과 능력치를 유지하면서 선택한 프로필 프리셋을 저장한다. */
"use client";
import { useEffect, useState } from "react";
import type { Character, RunAction } from "../../lib/types";
import { DEFAULT_APPEARANCE, type Appearance } from "../../lib/appearance";
import { AppearanceEditor } from "./AppearanceEditor";
export function CharacterCustomization({
  character,
  busy,
  run,
  save,
}: {
  character: Character;
  busy: boolean;
  run: RunAction;
  save: (appearance: Appearance) => Promise<void>;
}) {
  /* 선택한 프로필 프리셋을 저장한다. */

  const [appearance, setAppearance] = useState<Appearance>({
    ...DEFAULT_APPEARANCE,
    ...character.appearance,
  });
  const savedPreset = character.appearance?.preset ?? DEFAULT_APPEARANCE.preset;
  useEffect(() => {
    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setAppearance({
      preset: savedPreset,
    });
  }, [character.id, savedPreset]);
  return (
    <section className="panel customization-panel">
      <h2>프로필 선택</h2>
      <AppearanceEditor
        value={appearance}
        onChange={setAppearance}
        disabled={busy}
      />
      <button
        className="primary"
        disabled={busy}
        onClick={() => {
          /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void run(
            () => {
              /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return save(
                appearance,
              );
            },
          );
        }}
      >
        프로필 저장
      </button>
    </section>
  );
}
