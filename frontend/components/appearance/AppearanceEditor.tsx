/* 완성형 프로필 미리보기와 프리셋 선택 버튼을 표시한다. */
"use client";
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
    <section className="appearance-editor" aria-label="프로필 선택">
      <div className="pixel-stage">
        <PixelCharacter appearance={value} />
      </div>
      <div className="portrait-presets" role="group" aria-label="프로필 프리셋">
        {PORTRAITS.map((portrait) => {
          /* 각 항목의 화면 요소를 반환한다. */ return (
            <button
              type="button"
              key={portrait.id}
              disabled={disabled}
              aria-label={portrait.label}
              aria-pressed={portraitFor(value).id === portrait.id}
              onClick={() => {
                /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return onChange(
                  { ...value, preset: portrait.id },
                );
              }}
            >
              <img src={portrait.src} alt="" width={256} height={256} />
              {portraitFor(value).id === portrait.id && (
                <span className="portrait-check" aria-hidden="true">
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
