/* 상단 로그인 버튼에서 여는 인증 모달. Escape·닫기·로그인 성공 시 닫고 포커스를 복원한다. */
"use client";

import styles from "./Auth.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import { useEffect, useRef } from "react";
import type { useGame } from "../../hooks/useGame";
import { AuthPanel } from "./AuthPanel";
export function AuthModal({
  open,
  close,
  game,
}: {
  open: boolean;
  close: () => void;
  game: ReturnType<typeof useGame>;
}) {
  /* 인증 창을 열고 닫으며 로그인 성공 시 호출자에게 알린다. */

  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const element = dialog.current;
    game.setNotice("");
    element?.showModal();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      element?.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [open, game.setNotice]);
  return (
    <dialog
      ref={dialog}
      className={styles.authModal}
      aria-labelledby="auth-modal-title"
      onCancel={close}
    >
      <div className={styles.authModalHeading}>
        <h2 id="auth-modal-title">주무관 인증</h2>
        <button
          type="button"
          aria-label="인증 창 닫기"
          onClick={close}
        >
          닫기 ×
        </button>
      </div>
      {open && (
        <AuthPanel
          busy={game.busy}
          run={game.run}
          notify={game.setNotice}
          login={async (username, password) => {
            /* 비동기 요청 결과를 처리한다. */

            await game.login(username, password);
            close();
          }}
        />
      )}
      {game.notice && (
        <div
          role="status"
          className={sharedStyles.message}
          data-ui="message"
        >
          {game.notice}
        </div>
      )}
    </dialog>
  );
}
