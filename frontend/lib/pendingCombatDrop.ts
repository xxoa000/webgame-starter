/* 서버의 승리→발견 이벤트 순서로 대기 중인 전리품을 일반 파밍과 구분한다. */
import type { ExplorationState } from "./exploration";
export function pendingCombatDrop(state: ExplorationState | null) {
  /* 창을 열거나 물품을 버린 이벤트가 뒤에 붙어도 마지막 발견의 출처를 유지한다. */
  if (!state?.pending_item) return null;
  const found = state.history.findLastIndex((event) => event.kind === "found");
  return found > 0 && state.history[found - 1].kind === "victory"
    ? state.pending_item
    : null;
}
