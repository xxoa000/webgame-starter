/* 더 이상 불러오지 않는 기존 CSS만 제거한다. 환경 파일과 다른 파일은 건드리지 않는다. */
import { unlink, rmdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const oldFiles = [
  "styles/auth.css",
  "styles/base.css",
  "styles/bureau/appearance.css",
  "styles/bureau/base.css",
  "styles/bureau/combat.css",
  "styles/bureau/dashboard.css",
  "styles/bureau/drone-observation.css",
  "styles/bureau/dual-console.css",
  "styles/bureau/exploration-control.css",
  "styles/bureau/field-terminal.css",
  "styles/bureau/field.css",
  "styles/bureau/layout.css",
  "styles/bureau/personality.css",
  "styles/bureau/personnel.css",
  "styles/bureau/posts.css",
  "styles/bureau/rescue-shop.css",
  "styles/bureau/responsive.css",
  "styles/bureau/retro-terminal.css",
  "styles/characters.css",
  "styles/exploration.css",
  "styles/layout.css",
  "styles/refinements.css",
  "styles/responsive.css",
];

for (const file of oldFiles) {
  try {
    await unlink(path.join(root, file));
    console.log(`기존 스타일 제거: ${file}`);
  } catch (error) {
    // 이미 정리한 프로젝트에서도 재실행할 수 있다.
    if (error.code !== "ENOENT") throw error;
  }
}

// 사용자 CSS가 남아 있다면 폴더를 보존한다.
try {
  await rmdir(path.join(root, "styles/bureau"));
} catch (error) {
  if (!["ENOENT", "ENOTEMPTY"].includes(error.code)) throw error;
}
