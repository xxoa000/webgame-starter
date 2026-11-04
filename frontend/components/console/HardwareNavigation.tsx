/* 하단 물리 버튼 메뉴. 현재 경로의 버튼만 점등하며 홈은 기관 로고로 접근한다. */
"use client";

import styles from "./Console.module.css";
import { classNames } from "../../lib/classNames";
import Link from "next/link";
import { usePathname } from "next/navigation";
const menus = [
  {
    href: "/about",
    label: "기관 소개",
  },
  {
    href: "/character",
    label: "피계약자",
  },
  {
    href: "/explore",
    label: "균열 탐색",
  },
  {
    href: "/posts",
    label: "게시판",
  },
  {
    href: "/shop",
    label: "상점",
  },
];
export function HardwareNavigation() {
  /* 현재 페이지에 해당하는 물리 메뉴를 점등한다. */

  const pathname = usePathname();
  return (
    <nav
      className={styles.hardwareNav}
      aria-label="주요 메뉴"
    >
      {menus.map((menu) => {
        const active =
          pathname === menu.href || pathname.startsWith(menu.href + "/");
        return (
          <Link
            key={menu.href}
            href={menu.href}
            className={classNames(
              styles.hardwareMenu,
              menu.href === "/explore" ? styles.explorationMenu : "",
              active ? styles.isActive : "",
            )}
            aria-current={active ? "page" : undefined}
            data-ui={classNames(
              menu.href === "/explore" ? "" : "",
              active ? "" : "",
            )}
          >
            <span
              className={styles.hardwareButton}
              aria-hidden="true"
            >
              <span />
            </span>
            <span className={styles.hardwareLabel}>{menu.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}
