/* 겉성격·속성격·성향에서 하나씩 선택하는 입력을 표시한다. */
"use client";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import {
  PERSONALITY_CATEGORIES,
  PERSONALITY_LABELS,
  type PersonalityKeyword,
} from "../../lib/personality";
type Props = {
  value: number[];
  onChange: (value: number[]) => void;
  disabled?: boolean;
};
export function PersonalityPicker({
  value,
  onChange,
  disabled = false,
}: Props) {
  /* 서버에 등록된 분류별 키워드만 선택지로 사용한다. */
  const [choices, setChoices] = useState<PersonalityKeyword[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    /* 비동기 응답이 닫힌 폼의 상태를 갱신하지 않게 한다. */
    let active = true;
    void api<PersonalityKeyword[]>("/personality/keywords")
      .then((rows) => {
        /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
        if (active) setChoices(rows);
      })
      .catch((error: unknown) => {
        /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
        if (active)
          setError(error instanceof Error ? error.message : "성격 조회 실패");
      });
    return () => {
      /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
      active = false;
    };
  }, []);
  return (
    <fieldset disabled={disabled} className="personality-picker">
      <legend>성격</legend>
      {PERSONALITY_CATEGORIES.map((category) => {
        /* 각 분류의 선택값을 서로 독립적으로 유지한다. */
        const current = value.find((id) => {
          /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return choices.some(
            (row) => {
              /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
                row.id === id && row.category === category
              );
            },
          );
        });
        return (
          <label key={category}>
            {PERSONALITY_LABELS[category]}
            <select
              required
              value={current ?? ""}
              onChange={(event) => {
                /* 동일 분류의 이전 선택만 교체한다. */
                const ids = new Set(
                  choices
                    .filter((row) => {
                      /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
                        row.category === category
                      );
                    })
                    .map((row) => {
                      /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return row.id;
                    }),
                );
                onChange([
                  ...value.filter((id) => {
                    /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return !ids.has(
                      id,
                    );
                  }),
                  Number(event.target.value),
                ]);
              }}
            >
              <option value="" disabled>
                선택
              </option>
              {choices
                .filter((row) => {
                  /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
                    row.category === category
                  );
                })
                .map((row) => {
                  /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
                    <option key={row.id} value={row.id}>
                      {row.name}
                    </option>
                  );
                })}
            </select>
          </label>
        );
      })}
      {error && <small role="alert">{error}</small>}
    </fieldset>
  );
}
