/* 이벤트 결정 수집·공유 보스 공격·정산 결과를 표시한다. */
import type { RaidEvent } from "../../lib/raids";
import { itemFrame } from "../items/ItemIndicators";
import styles from "./RaidPanel.module.css";

type Props = {
  raid: RaidEvent;
  canAttack: boolean;
  busy: boolean;
  onAttack: () => void;
};

export function RaidPanel({ raid, canAttack, busy, onAttack }: Props) {
  /* 포인트는 이벤트 종료 시 서버에서 한 번만 자동 지급한다. */
  return (
    <section className={styles.panel} aria-label="공유 균열 레이드">
      <h3>
        {raid.status === "closed" ? "균열 봉쇄 완료" : "균열 경보"} ·{" "}
        {raid.map_name}
      </h3>
      <p>이벤트 지역 몬스터 조우 증가 · 균열 결정 발견 확률 1%</p>
      <p>
        지역 결정 회수 {raid.collected} / {raid.threshold} ·{" "}
        {raid.status === "collecting"
          ? "목표 달성 시 보스 출현"
          : raid.boss_name}
      </p>
      <div className={`${styles.crystal} ${itemFrame("mythic")}`}>
        <strong>균열 결정 · 미스틱</strong>
        <span>
          {raid.status === "closed" ? "변환 완료" : "내 전용 보관함"}{" "}
          {raid.my_items}개 ·{" "}
          {raid.status === "closed"
            ? "정산에 반영됨"
            : "종료 시 개당 스탯 포인트 +1"}
        </span>
      </div>
      {raid.status === "boss" && (
        <>
          <label className={styles.health}>
            공유 보스 HP {raid.boss_hp} / {raid.boss_max_hp}
            <progress max={raid.boss_max_hp} value={raid.boss_hp} />
          </label>
          <button disabled={busy || !canAttack} onClick={onAttack}>
            보스 공격 · 스태미나 소모 없음
          </button>
          {!canAttack && (
            <p>
              이 지역 탐사 중에 일반 전투·발견 물자를 처리하면 참가할 수 있어.
            </p>
          )}
        </>
      )}
      <p>참가 +1 · 최대 피해 +3 · 마지막 타격 +1 스탯 포인트 (중첩 지급)</p>
      <small>
        실제 피해를 입히면 참가로 인정하며, 최대 피해 동률은 공동 1위로 처리해.
      </small>
      {raid.status === "closed" && (
        <p role="status">내 지급 포인트 +{raid.my_reward} · 결정 변환 포함</p>
      )}
      {raid.leaders.length > 0 && (
        <ol>
          {raid.leaders.map((member, index) => (
            <li key={`${index}-${member.name}`}>
              {member.name} · 피해 {member.damage}
              {raid.status === "closed" ? ` · 포인트 +${member.reward}` : ""}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
