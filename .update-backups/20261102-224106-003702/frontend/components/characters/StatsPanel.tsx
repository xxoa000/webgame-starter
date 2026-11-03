import type { Character, StatRanges } from "../../lib/types";
import { CORE_STATS, STAT_LABELS, STAT_ORDER } from "../../lib/stats";

type Props = {
  character: Character;
  ranges: StatRanges;
  busy: boolean;
  reroll: () => void;
};

export function StatsPanel({ character, ranges, busy, reroll }: Props) {
  const ready = character.status === "ready";
  const total = CORE_STATS.reduce(
    (sum, key) => sum + (character.stats[key] ?? 0),
    0,
  );
  return (
    <section className="panel stats">
      <div className="stat-title">
        <div>
          <div className="mini">
            {ready ? "CHARACTER STATS" : "02 / ABILITIES"}
          </div>
          <h2>타고난 가능성</h2>
        </div>
        <span className="badge">{ready ? "FINAL" : "RANDOM"}</span>
      </div>
      <p className="muted">
        기본 스탯 5개의 합계는 20이야. 외모와 키는 별도로 추첨돼.
      </p>
      <div className="stat-list">
        {STAT_ORDER.map((key) => {
          const value = character.stats[key];
          const [minimum, maximum] =
            ranges[key] ??
            (key === "height_cm"
              ? [140, 200]
              : key === "appearance"
                ? [1, 100]
                : [1, 16]);
          const width = Math.max(
            2,
            Math.min(
              100,
              ((value - minimum) / Math.max(1, maximum - minimum)) * 100,
            ),
          );
          return (
            <div className="stat" key={key}>
              <div>
                <span>{STAT_LABELS[key]}</span>
                <small>
                  {minimum}–{maximum}
                  {key === "height_cm" ? " cm" : ""}
                </small>
                <strong>
                  {value}
                  <em>{key === "height_cm" ? " cm" : ""}</em>
                </strong>
              </div>
              <div className="track">
                <div style={{ width: `${width}%` }} />
              </div>
            </div>
          );
        })}
      </div>
      <div className="stat-total">
        <span>기본 스탯 합계</span>
        <strong>
          {total} <small>/ 20</small>
        </strong>
      </div>
      {!ready && (
        <div className="reroll">
          <div>
            <strong>새로운 가능성 찾기</strong>
            <p>이전 스탯으로 돌아갈 수 없어.</p>
          </div>
          <button
            disabled={busy || character.rerolls_remaining === 0}
            onClick={reroll}
          >
            ⟳ 전체 재추첨 <b>{character.rerolls_remaining}/10</b>
          </button>
        </div>
      )}
      <div className="hint">
        {ready
          ? `추가 재추첨 ${character.rerolls_used}회 사용 · 최종 확정된 능력치야.`
          : "새로고침해도 추첨 결과와 남은 횟수는 유지돼."}
      </div>
    </section>
  );
}
