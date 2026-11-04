/* 공통 보조 창: 프로필·인벤토리·도감을 열고 원래 화면으로 복귀한다. 탐색 상태는 유지한다. */
"use client";

import styles from "./Exploration.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useRef, type ReactNode } from "react";
import { usePathname } from "next/navigation";
const windowStyles: Record<string, string> = {
  inventory: styles.inventoryWindow,
  profile: "",
};
type Props = {
  title: string;
  kind: "inventory" | "profile";
  close: () => void;
  children: ReactNode;
};
export function Subwindow({ title, kind, close, children }: Props) {
  /* 보조 창을 열고 닫을 때 탐색 데이터는 그대로 유지한다. */

  const ref = useRef<HTMLDialogElement>(null);
  const exploring = usePathname().startsWith("/explore");
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={classNames(styles.exploreSubwindow, windowStyles[kind])}
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <div className={styles.subwindowHeader}>
        <div>
          <div
            className={sharedStyles.eyebrow}
            data-ui="eyebrow"
          >
            명령 입력 일시정지
          </div>
          <h2>{title}</h2>
        </div>
        <button
          onClick={close}
          autoFocus
          aria-label="보조 창 닫기"
        >
          ✕
        </button>
      </div>
      <p className={styles.subwindowNote}>
        현장 진행 상태를 유지하고 있습니다. 창을 닫으면 명령 입력으로
        복귀합니다.
      </p>
      {children}
      <button
        className={styles.subwindowReturn}
        onClick={close}
      >
        {exploring ? "탐색으로 돌아가기 →" : "원래 화면으로 돌아가기 →"}
      </button>
    </dialog>
  );
}
