/* 소유자에게 발화·속마음·행동 서술을 서로 구분해 표시한다. */
import type { ScriptOutput } from "../../lib/exploration";
const LABELS = { SPEECH: "발화", THOUGHT: "속마음", NARRATION: "행동" };
export function ScriptLines({ outputs }: { outputs?: ScriptOutput[] }) {
  /* 탐색 API는 소유자만 접근하며 공개 응답은 향후 별도로 구성한다. */
  if (!outputs?.length) return null;
  return (
    <div className="script-lines">
      {outputs.map((row) => {
        /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
          <p
            key={`${row.layer}-${row.script_id}`}
            className={`script-${row.layer.toLowerCase()}`}
          >
            <small>{LABELS[row.layer]}</small>
            {row.content}
          </p>
        );
      })}
    </div>
  );
}
