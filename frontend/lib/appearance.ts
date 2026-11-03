/* 완성형 프로필 프리셋과 기본 선택값을 정의한다. */
export type Appearance = { preset?: PortraitPreset };
export const DEFAULT_APPEARANCE: Appearance = { preset: "portrait_01" };
export const PORTRAITS = Array.from({ length: 6 }, (_, index) => ({
  id: `portrait_0${index + 1}` as PortraitPreset,
  src: `/portraits/portrait-0${index + 1}.png`,
  label: `프로필 ${index + 1}`,
}));
export type PortraitPreset =
  | "portrait_01"
  | "portrait_02"
  | "portrait_03"
  | "portrait_04"
  | "portrait_05"
  | "portrait_06";
export function portraitFor(appearance?: Appearance | null) {
  return PORTRAITS.find((p) => p.id === appearance?.preset) ?? PORTRAITS[0];
}
