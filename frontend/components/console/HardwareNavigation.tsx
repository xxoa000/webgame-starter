/* 하단 물리 버튼 메뉴. 현재 경로의 버튼만 점등하며 홈은 기관 로고로 접근한다. */
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
const menus = [
  { href: "/about", label: "기관 소개" },
  { href: "/character", label: "피계약자" },
  { href: "/explore", label: "균열 탐색" },
  { href: "/posts", label: "게시판" },
];
export function HardwareNavigation() {
  /* 현재 페이지에 해당하는 물리 메뉴를 점등한다. */

  const pathname = usePathname();
  return (
    <nav className="hardware-nav" aria-label="주요 메뉴">
      {menus.map((menu) => {
        /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

        const active =
          pathname === menu.href || pathname.startsWith(menu.href + "/");
        return (
          <Link
            key={menu.href}
            href={menu.href}
            className={`hardware-menu ${menu.href === "/explore" ? "exploration-menu" : ""} ${active ? "is-active" : ""}`}
            aria-current={active ? "page" : undefined}
          >
            <span className="hardware-button" aria-hidden="true">
              <span />
            </span>
            <span className="hardware-label">{menu.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
