// 세계관·UI 용어. 실제 승격/사망/전투 규칙과 DB 필드는 이 파일이 변경하지 않는다.
export const AGENCY = "차원위상격리감시국";
export const DEPARTMENTS = [
  {
    id: "01",
    name: "상황관제탑",
    role: "주무관 · 사용자",
    description: "원격 명령과 균열 대응을 총괄한다.",
    tone: "control",
  },
  {
    id: "02",
    name: "현장대응센터",
    role: "피계약자 소속",
    description: "균열 내부의 탐색과 현장 대응을 담당한다.",
    tone: "field",
  },
  {
    id: "03",
    name: "이능연구소",
    role: "NPC 기관",
    description: "이능과 차원 이상 현상을 연구한다.",
    tone: "research",
  },
  {
    id: "04",
    name: "질병관리청 특수오염대응과",
    role: "NPC 기관",
    description: "균열 독기와 특수 오염에 대응한다.",
    tone: "hazard",
  },
];
export function regionDescription(id: number) {
  return id === 1
    ? "붕괴 세계의 외곽 삼림. 민간인 피계약자의 초기 탐색 구역."
    : id === 3
      ? "균열 안쪽의 심층 삼림. 잔류 이능에 변이된 자원을 관측할 수 있다."
      : "균열 내부의 미확인 구역. 현장 안전을 우선하며 탐색한다.";
}
export function reportText(
  event: { kind: string; message: string },
  mapName: string,
) {
  if (event.kind === "start")
    return `${mapName} 진입. 주무관의 원격 명령 대기를 시작합니다.`;
  if (event.kind === "empty")
    return "구역 탐색 완료. 회수 가능한 자원은 발견되지 않았습니다.";
  if (event.kind === "end")
    return "현장 탐색을 종료했습니다. 회수한 물품은 인벤토리에 보관됩니다.";
  return event.message
    .replace("나무 그늘에 앉아 잠시 숨을 골랐다.", "안전 지점에서 휴식합니다.")
    .replace("숨을 골랐다.", "휴식 보고:")
    .replace("숲은 고요하다.", "추가 이상 징후 없음.");
}
