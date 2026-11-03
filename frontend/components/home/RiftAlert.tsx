/* 진행 중인 균열 이벤트만 재난 경보로 표시하고 봉쇄 진행률을 제한한다. */
import type { RiftEvent } from "../../lib/control";
export function RiftAlert({ events }: { events: RiftEvent[] }) {
  /* 화면 상태를 확인하고 RiftAlert 기능을 실행한다. */

  if (!events.length) return null;
  return (
    <section className="rift-alerts" aria-label="진행 중인 균열 경보">
      {events.map((event) => {
        /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

        const progress = Math.max(
          0,
          Math.min(100, Number.isFinite(event.progress) ? event.progress : 0),
        );
        return (
          <article className="rift-alert" key={event.id}>
            <div className="alarm-marker" aria-hidden="true">
              !
            </div>
            <div className="alarm-copy">
              <span className="mini">WARNING / 재난 경보</span>
              <h2>
                {event.name} · {event.location}
              </h2>
              <p>{event.objective}</p>
            </div>
            <div className="alarm-progress">
              <strong>봉쇄 진행 {progress}%</strong>
              <progress
                max={100}
                value={progress}
                aria-label={`${event.name} 봉쇄 진행률`}
              />
              <small>
                종료{" "}
                {new Date(event.endsAt).toLocaleString("ko-KR", {
                  timeZone: "Asia/Seoul",
                })}{" "}
                (KST)
              </small>
            </div>
          </article>
        );
      })}
    </section>
  );
}
