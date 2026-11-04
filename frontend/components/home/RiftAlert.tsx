/* 진행 중인 균열 이벤트만 재난 경보로 표시하고 봉쇄 진행률을 제한한다. */
import styles from "./Home.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import type { RiftEvent } from "../../lib/control";
export function RiftAlert({ events }: { events: RiftEvent[] }) {
  /* 진행 중인 균열이 있을 때만 홈 경보를 표시한다. */

  if (!events.length) return null;
  return (
    <section className={styles.riftAlerts} aria-label="진행 중인 균열 경보">
      {events.map((event) => {
        const progress = Math.max(
          0,
          Math.min(100, Number.isFinite(event.progress) ? event.progress : 0),
        );
        return (
          <article className={styles.riftAlert} key={event.id}>
            <div className={styles.alarmMarker} aria-hidden="true">
              !
            </div>
            <div className={styles.alarmCopy}>
              <span className={sharedStyles.smallLabel} data-ui="smallLabel">
                WARNING / 재난 경보
              </span>
              <h2>
                {event.name} · {event.location}
              </h2>
              <p>{event.objective}</p>
            </div>
            <div className={styles.alarmProgress}>
              <strong>봉쇄 진행 {progress}%</strong>
              <progress
                max={100}
                value={progress}
                aria-label={`${event.name} 봉쇄 진행률`}
              />
              {event.endsAt ? (
                <small>
                  종료{" "}
                  {new Date(event.endsAt).toLocaleString("ko-KR", {
                    timeZone: "Asia/Seoul",
                  })}{" "}
                  (KST)
                </small>
              ) : (
                <small>공유 보스 처치 시 균열 봉쇄</small>
              )}
            </div>
          </article>
        );
      })}
    </section>
  );
}
