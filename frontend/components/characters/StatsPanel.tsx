/* 캐릭터 능력치와 재추첨 조작을 표시한다. */
import { ResourceBars } from "./ResourceBars";
import type { Character, StatRanges } from "../../lib/types";
import { CORE_STATS, STAT_LABELS, STAT_ORDER } from "../../lib/stats";

type Props = {
  character: Character;
  ranges: StatRanges;
  busy: boolean;
  reroll: () => void;
};

export function StatsPanel({ character, ranges, busy, reroll }: Props) {
  /* 캐릭터 능력치와 재추첨 조작을 표시한다. */

  const ready = character.status === "ready";
  const total = CORE_STATS.reduce((sum, key) => {
    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
      sum + (character.stats[key] ?? 0)
    );
  }, 0);
  return (
    <section className="panel stats">
      <div className="stat-title">
        <div>
          <div className="mini">
            {ready ? "CAPABILITY REPORT" : "02 / 초기 능력 평가"}
          </div>
          <h2>현장 능력 평가</h2>
        </div>
        <span className="badge">{ready ? "확정" : "평가 중"}</span>
      </div>
      <p className="muted">기본 스탯 5개의 합계는 20이야.</p>
      {ready && <ResourceBars vitals={character.vitals} />}
      <div className="stat-list">
        {STAT_ORDER.map((key) => {
          /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

          const value = character.stats[key];
          const [minimum, maximum] = ranges[key] ?? [1, 16];
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
                </small>
                <strong>{value}</strong>
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
            <strong>초기 능력 재평가</strong>
            <p>이전 스탯으로 돌아갈 수 없어.</p>
          </div>
          <button
            disabled={busy || character.rerolls_remaining === 0}
            onClick={reroll}
          >
            ⟳ 능력 재추첨 <b>{character.rerolls_remaining}/10</b>
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
