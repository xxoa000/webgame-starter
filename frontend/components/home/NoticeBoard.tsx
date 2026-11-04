/* 백엔드의 활성 공지를 조회해 제목과 펼침 본문을 표시한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Home.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";
import type { Post, PostPage } from "../../lib/posts";
export function NoticeBoard() {
  /* 화면 진입 시 최신 공지 5개를 불러온다. */
  const [notices, setNotices] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    /* 언마운트된 화면에 응답을 적용하지 않는다. */
    let active = true;
    void api<PostPage>("/posts/notices?page_size=5")
      .then((data) => {
        if (active) setNotices(data.items);
      })
      .catch((error: unknown) => {
        if (active)
          setError(error instanceof Error ? error.message : "공지 조회 실패");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <section
      className={classNames(sharedStyles.panel, styles.noticeBoard)}
      aria-labelledby="notice-heading"
      data-ui="panel"
    >
      <div className={styles.consolePanelHeading}>
        <h2 id="notice-heading">관제 공지사항</h2>
        <Link href="/posts">게시판 →</Link>
      </div>
      {loading ? (
        <p>불러오는 중…</p>
      ) : error ? (
        <p role="alert">{error}</p>
      ) : !notices.length ? (
        <p>등록된 공지 없음</p>
      ) : (
        <div className={styles.noticeRows}>
          {notices.map((notice) => {
            return (
              <details key={notice.id}>
                <summary>
                  <span>{notice.title}</span>
                  <span
                    className={styles.noticeExpand}
                    aria-hidden="true"
                  >
                    ＋
                  </span>
                </summary>
                <div
                  className={classNames(
                    styles.bulletinBody,
                    sharedStyles.postContent,
                  )}
                >
                  {notice.content}
                </div>
              </details>
            );
          })}
        </div>
      )}
    </section>
  );
}
