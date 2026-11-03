/* 피계약자를 중계하는 관제 드론을 표시한다. */
// 코드로 그린 중계 드론. 장식용으로 별도의 이미지 의존성이 없다.
export function RelayDrone({ large = false }: { large?: boolean }) {
  /* 피계약자를 중계하는 관제 드론을 표시한다. */

  return (
    <div className={`relay-drone ${large ? "large" : ""}`} aria-hidden="true">
      <div className="drone-orbit" />
      <div className="drone-body">
        <span className="drone-lens" />
        <span className="drone-light" />
      </div>
      <div className="drone-shadow" />
    </div>
  );
}
