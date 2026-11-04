/* 메인 콘솔에는 현재 페이지의 작업 영역만 배치한다. */
"use client";

import styles from "./Console.module.css";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
export function MainConsole({
  children,
}: {
  ready: boolean;
  children: ReactNode;
}) {
  /* 인벤토리·도감은 서브 콘솔에서 표시한다. */
  const pathname = usePathname();
  return (
    <div className={styles.mainScreenLayout}>
      <div
        key={pathname}
        className={styles.mainWorkspace}
      >
        {children}
      </div>
    </div>
  );
}
