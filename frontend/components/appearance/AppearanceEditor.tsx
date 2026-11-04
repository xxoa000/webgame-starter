/* 완성형 프로필 미리보기와 프리셋 선택 버튼을 표시한다. */
"use client";

import styles from "../characters/Characters.module.css";
import { PixelCharacter } from "./PixelCharacter";
import { PORTRAITS, portraitFor, type Appearance } from "../../lib/appearance";
export function AppearanceEditor({
  value,
  onChange,
  disabled = false,
}: {
  value: Appearance;
  onChange: (value: Appearance) => void;
  disabled?: boolean;
}) {
  /* 프로필 이미지 선택과 미리보기를 제공한다. */

  return (
    <section
      className={styles.appearanceEditor}
      aria-label="프로필 선택"
    >
      <div className={styles.pixelStage}>
        <PixelCharacter appearance={value} />
      </div>
      <div
        className={styles.portraitPresets}
        role="group"
        aria-label="프로필 프리셋"
      >
        {PORTRAITS.map((portrait) => {
          return (
            <button
              type="button"
              key={portrait.id}
              disabled={disabled}
              aria-label={portrait.label}
              aria-pressed={portraitFor(value).id === portrait.id}
              onClick={() => {
                return onChange({
                  ...value,
                  preset: portrait.id,
                });
              }}
            >
              <img
                src={portrait.src}
                alt=""
                width={256}
                height={256}
              />
              {portraitFor(value).id === portrait.id && (
                <span
                  className={styles.portraitCheck}
                  aria-hidden="true"
                >
                  ✓
                </span>
              )}
            </button>
          );
        })}
      </div>
    </section>
  );
}
