/* 소유자에게 발화·속마음·행동 서술을 서로 구분해 표시한다. */
import styles from "./Exploration.module.css";
import type { ScriptOutput } from "../../lib/exploration";
const scriptStyles: Record<string, string> = {
  SPEECH: "",
  THOUGHT: styles.thought,
  NARRATION: styles.narration,
};
export function ScriptLines({ outputs }: { outputs?: ScriptOutput[] }) {
  /* 탐색 API는 소유자만 접근하며 공개 응답은 향후 별도로 구성한다. */
  // 속마음은 서브 콘솔에서 표시하므로 이 목록에서 제외한다.
  // 발화는 화면에서 따옴표를 한 번만 붙이고 DB 원문은 수정하지 않는다.
  if (!outputs?.length) return null;
  return (
    <div className={styles.scriptLines}>
      {outputs
        .filter((row) => row.layer !== "THOUGHT")
        .map((row) => {
          return (
            <p
              key={`${row.layer}-${row.script_id}`}
              className={scriptStyles[row.layer]}
            >
              {row.layer === "SPEECH"
                ? `"${row.content.trim().replace(/^["“]([\s\S]*)["”]$/, "$1")}"`
                : row.content}
            </p>
          );
        })}
    </div>
  );
}
