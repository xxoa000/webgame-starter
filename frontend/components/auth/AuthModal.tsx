/* 상단 로그인 버튼에서 여는 인증 모달. Escape·닫기·로그인 성공 시 닫고 포커스를 복원한다. */
"use client";
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
  /* 화면 상태를 확인하고 AuthModal 기능을 실행한다. */

  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const element = dialog.current;
    game.setNotice("");
    element?.showModal();
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

      element?.close();
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [open, game.setNotice]);
  return (
    <dialog
      ref={dialog}
      className="auth-modal"
      aria-labelledby="auth-modal-title"
      onCancel={close}
    >
      <div className="auth-modal-heading">
        <h2 id="auth-modal-title">주무관 인증</h2>
        <button type="button" aria-label="인증 창 닫기" onClick={close}>
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
        <div role="status" className="notice">
          {game.notice}
        </div>
      )}
    </dialog>
  );
}
