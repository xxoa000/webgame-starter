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
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [checked, setChecked] = useState<string | null>(null);
  const revision = useRef(0);

  function submit(event: FormEvent) {
    event.preventDefault();
    void run(async () => {
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
    const candidate = username.toLowerCase();
    const version = revision.current;
    void run(async () => {
      const result = await api<{ available: boolean }>(
        "/auth/check-username?username=" + encodeURIComponent(candidate),
      );
      if (version !== revision.current) return;
      setChecked(result.available ? candidate : null);
      notify(
        result.available ? "사용 가능한 아이디야." : "이미 사용 중인 아이디야.",
      );
    });
  }
  return (
    <div className="entry-grid">
      <section className="intro panel">
        <div className="mini">CHARACTER SYSTEM / 01</div>
        <div className="orb">✧</div>
        <h2>
          아직 정해지지 않은
          <br />
          무한한 가능성.
        </h2>
        <p>
          세계는 준비 중이지만,
          <br />네 이야기는 지금 시작할 수 있어.
        </p>
        <div className="intro-foot">
          <span>
            07 <small>랜덤 능력치</small>
          </span>
          <span>
            10 <small>다시 선택할 기회</small>
          </span>
        </div>
      </section>
      <section className="panel auth">
        <div className="tabs">
          {(["login", "signup"] as const).map((value) => (
            <button
              key={value}
              disabled={busy}
              className={mode === value ? "selected" : ""}
              onClick={() => {
                setMode(value);
                notify("");
              }}
            >
              {value === "login" ? "로그인" : "회원가입"}
            </button>
          ))}
        </div>
        <h2>
          {mode === "login" ? "다시 만나서 반가워." : "첫 번째 페이지를 열어."}
        </h2>
        <p className="muted">나만의 캐릭터를 위한 계정.</p>
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
                  setUsername(event.target.value);
                  setChecked(null);
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
          </label>
          <label>
            비밀번호
            <input
              required
              type="password"
              minLength={10}
              maxLength={128}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
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
                onChange={(event) => setConfirmation(event.target.value)}
              />
            </label>
          )}
          <button disabled={busy} className="primary">
            {busy
              ? "처리 중…"
              : mode === "login"
                ? "로그인 →"
                : "계정 만들기 →"}
          </button>
        </form>
        <div className="secure">
          ◇ 비밀번호는 Argon2 해시로 안전하게 저장돼.
        </div>
      </section>
    </div>
  );
}
