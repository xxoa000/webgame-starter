/* 신원·남녀 성별·나이·공용 도트 외형을 함께 검증하고 피계약자를 등록한다. */
"use client";
import { useRef, useState, type FormEvent } from "react";
import { AppearanceEditor } from "../appearance/AppearanceEditor";
import { DEFAULT_APPEARANCE, type Appearance } from "../../lib/appearance";
import { PersonalityPicker } from "../personality/PersonalityPicker";
import { api } from "../../lib/api";
import type { ProfileInput, RunAction } from "../../lib/types";

type Props = {
  busy: boolean;
  run: RunAction;
  notify: (message: string) => void;
  finalize: (profile: ProfileInput) => Promise<void>;
};

export function CharacterForm({ busy, run, notify, finalize }: Props) {
  /* 캐릭터 신원과 프로필 입력을 검증해 등록한다. */

  const [personality, setPersonality] = useState<number[]>([]);
  const [name, setName] = useState("");
  const [gender, setGender] = useState<"male" | "female">("female");
  const [age, setAge] = useState(10);
  const [appearance, setAppearance] = useState<Appearance>({
    ...DEFAULT_APPEARANCE,
  });
  const [bio, setBio] = useState("");
  const [checkedName, setCheckedName] = useState<string | null>(null);
  const [fieldMessage, setFieldMessage] = useState("");
  const revision = useRef(0);
  const candidate = name.trim().normalize("NFC");

  function checkName() {
    /* 화면 상태를 확인하고 checkName 기능을 실행한다. */

    const version = revision.current;
    void run(async () => {
      /* 비동기 요청 결과를 처리한다. */

      try {
        const result = await api<{ available: boolean }>(
          "/characters/check-name?name=" + encodeURIComponent(candidate),
        );
        if (version !== revision.current) return;
        setCheckedName(result.available ? candidate : null);
        setFieldMessage(
          result.available
            ? "사용 가능한 피계약자 이름이야."
            : "이미 사용 중인 피계약자 이름이야.",
        );
      } catch (error) {
        if (version === revision.current)
          setFieldMessage((error as Error).message);
      }
    });
  }
  function submit(event: FormEvent<HTMLFormElement>) {
    /* 폼 기본 제출을 막고 검증된 입력으로 요청을 실행한다. */

    event.preventDefault();
    void run(async () => {
      /* 비동기 요청 결과를 처리한다. */

      if (checkedName !== candidate)
        throw new Error("피계약자 이름 중복 확인을 먼저 해.");
      if (personality.length !== 3)
        throw new Error("성격을 분류별로 하나씩 선택해.");
      await finalize({
        name: candidate,
        gender,
        age,
        bio,
        appearance,
        personality_keyword_ids: personality,
      });
    });
  }
  return (
    <form onSubmit={submit}>
      <div className="civilian-notice">
        <span>초기 배치</span>
        <strong>민간인 피계약자</strong>
        <p>
          첫 투입은 민간인입니다. 현장 경험과 능력은 대원 승격의 기반이 됩니다.
        </p>
      </div>
      <label>
        피계약자 이름
        <div className="inline">
          <input
            required
            maxLength={24}
            value={name}
            onChange={(event) => {
              /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

              setName(event.target.value);
              setCheckedName(null);
              setFieldMessage("");
              revision.current++;
            }}
            placeholder="이름을 입력해"
          />
          <button
            type="button"
            disabled={busy || !candidate}
            onClick={checkName}
          >
            중복 확인
          </button>
        </div>
        {fieldMessage && (
          <small
            className={`field-feedback ${checkedName ? "success" : "error"}`}
            role="status"
          >
            {fieldMessage}
          </small>
        )}
      </label>
      <label>
        성별
        <select
          value={gender}
          onChange={(event) => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setGender(
              event.target.value as "male" | "female",
            );
          }}
        >
          <option value="female">여자</option>
          <option value="male">남자</option>
        </select>
      </label>
      <label>
        나이
        <select
          value={age}
          onChange={(event) => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setAge(
              Number(event.target.value),
            );
          }}
        >
          {Array.from({ length: 41 }, (_, index) => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
              index + 10
            );
          }).map((value) => {
            /* 각 항목의 화면 요소를 반환한다. */ return (
              <option key={value} value={value}>
                {value}세
              </option>
            );
          })}
        </select>
      </label>
      <label>
        인적 사항 <small>선택</small>
        <textarea
          maxLength={500}
          rows={3}
          value={bio}
          onChange={(event) => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setBio(
              event.target.value,
            );
          }}
          placeholder="재난에 말려든 경위나 인적 사항을 기록하십시오."
        />
      </label>
      <PersonalityPicker
        value={personality}
        onChange={setPersonality}
        disabled={busy}
      />
      <AppearanceEditor
        value={appearance}
        onChange={setAppearance}
        disabled={busy}
      />
      <p className="hint">확정 후에는 스탯을 다시 뽑을 수 없어.</p>
      <button
        disabled={
          busy ||
          !candidate ||
          checkedName !== candidate ||
          personality.length !== 3
        }
        className="primary"
      >
        피계약자 등록 확정 →
      </button>
    </form>
  );
}
