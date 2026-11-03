/* 공통 계정 상태와 듀얼 물리 콘솔을 모든 경로에 제공하는 루트 레이아웃. */
import "./globals.css";
import { ConsoleDesk } from "../components/console/ConsoleDesk";
import type { Metadata } from "next";
export const metadata: Metadata = {
  title: "차원위상격리감시국 | 상황관제탑",
  description: "균열 너머의 피계약자와 연결되는 원격 관제 단말",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  /* 전체 페이지에 공통 콘솔 레이아웃을 적용한다. */

  return (
    <html lang="ko">
      <body>
        <ConsoleDesk>{children}</ConsoleDesk>
      </body>
    </html>
  );
}
