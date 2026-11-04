/* 선택한 완성형 프로필 이미지를 원본 색상으로 표시한다. */
import styles from "../characters/Characters.module.css";
import { classNames } from "../../lib/classNames";
import { portraitFor, type Appearance } from "../../lib/appearance";
export function PixelCharacter({
  appearance,
  compact = false,
}: {
  appearance?: Appearance | null;
  compact?: boolean;
}) {
  /* 선택한 프로필 이미지를 원본 색상으로 표시한다. */

  const portrait = portraitFor(appearance);
  return (
    <img
      src={portrait.src}
      alt={portrait.label}
      className={classNames(
        styles.pixelCharacter,
        compact ? styles.compact : "",
      )}
      width={512}
      height={512}
      data-ui={compact ? "" : ""}
    />
  );
}
