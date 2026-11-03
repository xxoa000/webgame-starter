"use client";
import { useRef, useState, type FormEvent } from "react";
import { api } from "../../lib/api";
import type { ProfileInput, RunAction } from "../../lib/types";

type Props = {
  busy: boolean;
  run: RunAction;
  notify: (message: string) => void;
  finalize: (profile: ProfileInput) => Promise<void>;
};

export function CharacterForm({ busy, run, notify, finalize }: Props) {
  const [name, setName] = useState("");
  const [gender, setGender] = useState("female");
  const [age, setAge] = useState(10);
  const [bio, setBio] = useState("");
  const [checkedName, setCheckedName] = useState<string | null>(null);
  const revision = useRef(0);
  const candidate = name.trim().normalize("NFC");

  function checkName() {
    const version = revision.current;
    void run(async () => {
      const result = await api<{ available: boolean }>(
        "/characters/check-name?name=" + encodeURIComponent(candidate),
      );
      if (version !== revision.current) return;
      setCheckedName(result.available ? candidate : null);
      notify(
        result.available
          ? "사용 가능한 캐릭터 이름이야."
          : "이미 사용 중인 캐릭터 이름이야.",
      );
    });
  }
  function submit(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
      if (checkedName !== candidate)
        throw new Error("캐릭터 이름 중복 확인을 먼저 해.");
      await finalize({ name: candidate, gender, age, bio });
    });
  }
  return (
    <form onSubmit={submit}>
      <label>
        캐릭터 이름
        <div className="inline">
          <input
            required
            maxLength={24}
            value={name}
            onChange={(event) => {
              setName(event.target.value);
              setCheckedName(null);
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
      </label>
      <label>
        성별
        <select
          value={gender}
          onChange={(event) => setGender(event.target.value)}
        >
          <option value="female">여성</option>
          <option value="male">남성</option>
          <option value="other">기타</option>
        </select>
      </label>
      <label>
        나이
        <select
          value={age}
          onChange={(event) => setAge(Number(event.target.value))}
        >
          {Array.from({ length: 8 }, (_, index) => index + 10).map((value) => (
            <option key={value} value={value}>
              {value}세
            </option>
          ))}
        </select>
      </label>
      <label>
        프로필 소개 <small>선택</small>
        <textarea
          maxLength={500}
          rows={3}
          value={bio}
          onChange={(event) => setBio(event.target.value)}
          placeholder="어떤 캐릭터인지 소개해."
        />
      </label>
      <p className="hint">확정 후에는 스탯을 다시 뽑을 수 없어.</p>
      <button
        disabled={busy || !candidate || checkedName !== candidate}
        className="primary"
      >
        이 캐릭터로 시작하기 →
      </button>
    </form>
  );
}
