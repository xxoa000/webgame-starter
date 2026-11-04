/* 투명 배경의 도트 관제 드론을 표시한다. */
import styles from "../console/Console.module.css";
import { classNames } from "../../lib/classNames";
export function RelayDrone({ large = false }: { large?: boolean }) {
  /* 원본 PNG의 픽셀 경계를 유지한다. */
  return (
    <div
      className={classNames(styles.relayDrone, large ? styles.large : "")}
      aria-hidden="true"
    >
      <img
        className={styles.droneSprite}
        src="/drone/relay-pixel.png"
        alt=""
        width={64}
        height={64}
      />
    </div>
  );
}
