/* 이름·나이의 남은 수정 기회와 무제한 인적사항 편집을 제공한다. */
"use client";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { useGame } from "../../hooks/useGame";
import { api } from "../../lib/api";
import type { Character, ProfileUpdate } from "../../lib/types";
export function CharacterIdentityEditor({
  character,
}: {
  character: Character;
}) {
  /* 확정된 신원과 서버의 남은 수정 횟수를 입력 폼에 반영한다. */
  const game = useGame();
  const [name, setName] = useState(character.name),
    [age, setAge] = useState<number | "">(character.age ?? "");
  const [gender, setGender] = useState<"male" | "female" | "">(
    character.gender === "male" || character.gender === "female"
      ? character.gender
      : "",
  );
  const [bio, setBio] = useState(character.bio),
    [checked, setChecked] = useState<string | null>(null),
    [message, setMessage] = useState("");
  const revision = useRef(0);
  useEffect(() => {
    /* 다른 화면에서 저장된 신원이 달라진 경우 입력값을 갱신한다. */
    setName(character.name);
    setAge(character.age ?? "");
    setGender(
      character.gender === "male" || character.gender === "female"
        ? character.gender
        : "",
    );
    setBio(character.bio);
    setChecked(null);
    setMessage("");
    revision.current++;
  }, [
    character.id,
    character.name,
    character.age,
    character.gender,
    character.bio,
  ]);
  const candidate = name.trim().normalize("NFC");
  async function checkName(): Promise<void> {
    /* 이전 입력의 중복 검사 응답이 현재 입력을 덮어쓰지 않게 한다. */
    const version = ++revision.current;
    await game.run(async () => {
      /* 비동기 요청 결과를 처리한다. */

      const result = await api<{ available: boolean }>(
        "/characters/check-name?for_profile=true&name=" + encodeURIComponent(candidate),
      );
      if (version !== revision.current) return;
      setChecked(result.available ? candidate : null);
      setMessage(
        result.available ? "사용 가능한 이름이야." : "이미 사용 중인 이름이야.",
      );
    });
  }
  function submit(event: FormEvent<HTMLFormElement>): void {
    /* 실제 변경된 필드만 전송해 동일 값 저장으로 기회를 소비하지 않는다. */
    event.preventDefault();
    void game.run(async () => {
      /* 비동기 요청 결과를 처리한다. */

      const patch: ProfileUpdate = { bio };
      if (gender && gender !== character.gender) patch.gender = gender;
      if (candidate !== character.name) {
        if (checked !== candidate) throw new Error("이름 중복 확인을 먼저 해.");
        patch.name = candidate;
      }
      if (age !== "" && age !== character.age) patch.age = age;
      await game.updateProfile(patch);
    });
  }
  return (
    <form className="panel identity-editor" onSubmit={submit}>
      <h2>인적사항 수정</h2>
      <label>
        이름 · 수정 가능 {character.name_changes_remaining}회
        <div className="inline">
          <input
            required
            value={name}
            maxLength={24}
            disabled={game.busy || character.name_changes_remaining === 0}
            onChange={(event) => {
              /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
              setName(event.target.value);
              setChecked(null);
              setMessage("");
              revision.current++;
            }}
          />
          <button
            type="button"
            disabled={
              game.busy ||
              character.name_changes_remaining === 0 ||
              !candidate ||
              candidate === character.name
            }
            onClick={() => {
              /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return void checkName();
            }}
          >
            중복 확인
          </button>
        </div>
        {message && (
          <small className="field-feedback" role="status">
            {message}
          </small>
        )}
      </label>
      <label>
        나이 · 수정 가능 {character.age_changes_remaining}회
        <select
          value={age}
          disabled={game.busy || character.age_changes_remaining === 0}
          onChange={(event) => {
            /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return setAge(
              Number(event.target.value),
            );
          }}
        >
          <option value="" disabled>
            선택
          </option>
          {Array.from({ length: 41 }, (_, i) => {
            /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return i + 10;
          }).map((value) => {
            /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
              <option key={value} value={value}>
                {value}세
              </option>
            );
          })}
        </select>
      </label>
      <label>
        성별
        <select
          disabled={game.busy}
          value={gender}
          onChange={(event) => {
            /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return setGender(
              event.target.value as "male" | "female",
            );
          }}
        >
          <option value="" disabled>
            선택
          </option>
          <option value="male">남자</option>
          <option value="female">여자</option>
        </select>
      </label>
      <label>
        인적사항
        <textarea
          maxLength={500}
          rows={4}
          disabled={game.busy}
          value={bio}
          onChange={(event) => {
            /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return setBio(
              event.target.value,
            );
          }}
        />
      </label>
      <button className="primary" disabled={game.busy}>
        인적사항 저장
      </button>
    </form>
  );
}
