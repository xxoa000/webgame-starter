/* 조건에 따라 여러 CSS Module 클래스를 결합한다. */
export function classNames(
  ...values: Array<string | false | null | undefined>
): string {
  /* 비활성 상태의 빈 값은 제외하고 클래스 이름만 연결한다. */
  return values.filter(Boolean).join(" ");
}
