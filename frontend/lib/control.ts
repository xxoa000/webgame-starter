/* 균열 이벤트의 표시 데이터와 활성 시간 검사를 정의한다. */
export type RiftEvent = {
  id: string;
  name: string;
  location: string;
  active: boolean;
  startsAt: string;
  endsAt: string;
  progress: number;
  objective: string;
};
// 실제 이벤트 운영 시 추가. progress는 봉쇄 진행률(0~100), 시간은 ISO 8601로 입력한다.
// 예: { id: "R-001", name: "도심 균열", location: "제1구역", active: true,
// startsAt: "2026-12-01T00:00:00+09:00", endsAt: "2026-12-02T00:00:00+09:00",
// progress: 25, objective: "잔존 위협을 제거하고 균열을 봉쇄하십시오." }
export const riftEvents: RiftEvent[] = [];
export function activeRifts(now: number): RiftEvent[] {
  return riftEvents.filter(
    (event) =>
      event.active &&
      Date.parse(event.startsAt) <= now &&
      now < Date.parse(event.endsAt),
  );
}
