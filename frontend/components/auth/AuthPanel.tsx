/* 기밀 관제 단말의 로그인·회원가입과 아이디 중복 확인을 처리한다. */
"use client";
import { useRef, useState, type FormEvent } from "react";
import { api } from "../../lib/api";
import type { RunAction } from "../../lib/types";

type Props = {
  busy: boolean;
  run: RunAction;
  notify: (message: string) => void;
  login: (username: string, password: string) => Promise<void>;
};

export function AuthPanel({ busy, run, notify, login }: Props) {
  /* 로그인과 회원가입 입력 상태 및 인증 요청을 처리한다. */

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [checked, setChecked] = useState<string | null>(null);
  const [fieldMessage, setFieldMessage] = useState("");
  const revision = useRef(0);

  function submit(event: FormEvent<HTMLFormElement>) {
    /* 폼 기본 제출을 막고 검증된 입력으로 요청을 실행한다. */

    event.preventDefault();
    void run(async () => {
      /* 비동기 요청 결과를 처리한다. */

      if (mode === "login") {
        await login(username, password);
        return;
      }
      if (checked !== username.toLowerCase())
        throw new Error("아이디 중복 확인을 먼저 해.");
      if (password !== confirmation)
        throw new Error("비밀번호 확인이 일치하지 않아.");
      await api("/auth/signup", { username, password });
      setMode("login");
      setPassword("");
      setConfirmation("");
      notify("가입 완료. 로그인해.");
    });
  }
  function checkUsername() {
    /* 현재 입력한 아이디의 중복 여부를 확인한다. */

    const candidate = username.toLowerCase();
    const version = revision.current;
    void run(async () => {
      /* 비동기 요청 결과를 처리한다. */

      try {
        const result = await api<{ available: boolean }>(
          "/auth/check-username?username=" + encodeURIComponent(candidate),
        );
        if (version !== revision.current) return;
        setChecked(result.available ? candidate : null);
        setFieldMessage(
          result.available
            ? "사용 가능한 아이디야."
            : "이미 사용 중인 아이디야.",
        );
      } catch (error) {
        if (version === revision.current)
          setFieldMessage((error as Error).message);
      }
    });
  }
  return (
    <section className="panel auth classified-auth">
      <div className="auth-classification">
        보안 구역 · AUTHORIZED PERSONNEL ONLY
      </div>
      <div className="tabs">
        {(["login", "signup"] as const).map((value) => {
          /* 각 항목의 화면 요소를 반환한다. */ return (
            <button
              key={value}
              disabled={busy}
              className={mode === value ? "selected" : ""}
              onClick={() => {
                /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

                setMode(value);
                notify("");
              }}
            >
              {value === "login" ? "로그인" : "회원가입"}
            </button>
          );
        })}
      </div>
      <h2>
        {mode === "login"
          ? "관제 세션에 접속합니다."
          : "주무관 계정을 등록합니다."}
      </h2>
      <p className="muted">상황관제탑 내부 시스템 · 개인 인증</p>
      <form onSubmit={submit}>
        <label>
          아이디
          <div className="inline">
            <input
              required
              pattern="[a-zA-Z0-9_]{4,24}"
              maxLength={24}
              autoComplete="username"
              value={username}
              onChange={(event) => {
                /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

                setUsername(event.target.value);
                setChecked(null);
                setFieldMessage("");
                revision.current++;
              }}
              placeholder="영문, 숫자, 밑줄 4~24자"
            />
            {mode === "signup" && (
              <button
                type="button"
                disabled={busy || !/^[a-zA-Z0-9_]{4,24}$/.test(username)}
                onClick={checkUsername}
              >
                중복 확인
              </button>
            )}
          </div>
          {mode === "signup" && fieldMessage && (
            <small
              className={`field-feedback ${checked ? "success" : "error"}`}
              role="status"
            >
              {fieldMessage}
            </small>
          )}
        </label>
        <label>
          비밀번호
          <input
            required
            type="password"
            minLength={10}
            maxLength={128}
            value={password}
            onChange={(event) => {
              /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setPassword(
                event.target.value,
              );
            }}
            autoComplete={
              mode === "login" ? "current-password" : "new-password"
            }
            placeholder="10자 이상 입력"
          />
        </label>
        {mode === "signup" && (
          <label>
            비밀번호 확인
            <input
              required
              type="password"
              autoComplete="new-password"
              value={confirmation}
              onChange={(event) => {
                /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setConfirmation(
                  event.target.value,
                );
              }}
            />
          </label>
        )}
        <button disabled={busy} className="primary">
          {busy
            ? "처리 중…"
            : mode === "login"
              ? "관제 접속 →"
              : "주무관 등록 →"}
        </button>
      </form>
      <div className="secure">
        개인 인증 필수 · 접속 권한을 타인과 공유하지 마십시오.
      </div>
    </section>
  );
}
