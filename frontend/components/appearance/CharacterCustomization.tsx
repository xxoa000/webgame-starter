/* 성별과 능력치를 유지하면서 선택한 프로필 프리셋을 저장한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "../characters/Characters.module.css";
import { classNames } from "../../lib/classNames";
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
    return setAppearance({
      preset: savedPreset,
    });
  }, [character.id, savedPreset]);
  return (
    <section
      className={classNames(sharedStyles.panel, styles.customizationPanel)}
      data-ui="panel"
    >
      <h2>프로필 선택</h2>
      <AppearanceEditor
        value={appearance}
        onChange={setAppearance}
        disabled={busy}
      />
      <button
        className={sharedStyles.primaryButton}
        disabled={busy}
        onClick={() => {
          return void run(() => {
            return save(appearance);
          });
        }}
        data-ui="primaryButton"
      >
        프로필 저장
      </button>
    </section>
  );
}
