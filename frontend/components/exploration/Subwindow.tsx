/* 공통 보조 창: 프로필·인벤토리·도감을 열고 원래 화면으로 복귀한다. 탐색 상태는 유지한다. */
"use client";
import { useEffect, useRef, type ReactNode } from "react";
import { usePathname } from "next/navigation";

type Props = {
  title: string;
  kind: "inventory" | "profile";
  close: () => void;
  children: ReactNode;
};

export function Subwindow({ title, kind, close, children }: Props) {
  /* 화면 상태를 확인하고 Subwindow 기능을 실행한다. */

  const ref = useRef<HTMLDialogElement>(null);
  const exploring = usePathname().startsWith("/explore");
  useEffect(() => {
    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

      dialog?.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`explore-subwindow ${kind}-window`}
      aria-label={title}
      onCancel={(event) => {
        /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

        event.preventDefault();
        close();
      }}
    >
      <div className="subwindow-header">
        <div>
          <div className="eyebrow">명령 입력 일시정지</div>
          <h2>{title}</h2>
        </div>
        <button onClick={close} autoFocus aria-label="보조 창 닫기">
          ✕
        </button>
      </div>
      <p className="subwindow-note">
        현장 진행 상태를 유지하고 있습니다. 창을 닫으면 명령 입력으로
        복귀합니다.
      </p>
      {children}
      <button className="subwindow-return" onClick={close}>
        {exploring ? "탐색으로 돌아가기 →" : "원래 화면으로 돌아가기 →"}
      </button>
    </dialog>
  );
}
