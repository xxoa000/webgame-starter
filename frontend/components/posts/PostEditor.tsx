/* 제목·본문과 운영자 전용 공지·상태 입력을 표시한다. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Posts.module.css";
import { classNames } from "../../lib/classNames";
import { useState, type FormEvent } from "react";
import {
  POST_STATUSES,
  type Post,
  type PostInput,
  type PostStatus,
} from "../../lib/posts";
type Props = {
  post?: Post;
  canManage: boolean;
  busy: boolean;
  save: (input: PostInput, id?: number) => Promise<boolean>;
  close: () => void;
};
export function PostEditor({ post, canManage, busy, save, close }: Props) {
  /* 수정 대상이 있으면 저장된 값으로 입력 폼을 초기화한다. */
  const [title, setTitle] = useState(post?.title ?? "");
  const [content, setContent] = useState(post?.content ?? "");
  const [notice, setNotice] = useState(post?.is_notice === 1);
  const [status, setStatus] = useState<PostStatus>(post?.post_status ?? 1);
  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    /* 일반 사용자의 요청에는 운영 필드를 포함하지 않는다. */
    event.preventDefault();
    const input: PostInput = {
      title,
      content,
    };
    if (canManage) {
      input.is_notice = notice ? 1 : 0;
      if (post) input.post_status = status;
    }
    if (await save(input, post?.id)) close();
  }
  return (
    <form
      className={classNames(sharedStyles.panel, styles.postEditor)}
      onSubmit={(event) => {
        return void submit(event);
      }}
      data-ui="panel"
    >
      <h2>{post ? "글 수정" : "글 작성"}</h2>
      <label>
        제목
        <input
          value={title}
          maxLength={200}
          required
          disabled={busy}
          onChange={(event) => {
            return setTitle(event.target.value);
          }}
        />
      </label>
      <label>
        본문
        <textarea
          value={content}
          maxLength={16000}
          required
          rows={12}
          disabled={busy}
          onChange={(event) => {
            return setContent(event.target.value);
          }}
        />
      </label>
      {canManage && (
        <>
          <label className={styles.postCheckbox}>
            <input
              type="checkbox"
              checked={notice}
              disabled={busy}
              onChange={(event) => {
                return setNotice(event.target.checked);
              }}
            />
            공지사항
          </label>
          {post && (
            <label>
              상태
              <select
                value={status}
                disabled={busy}
                onChange={(event) => {
                  return setStatus(Number(event.target.value) as PostStatus);
                }}
              >
                {Object.entries(POST_STATUSES).map(([key, label]) => {
                  return (
                    <option
                      value={key}
                      key={key}
                    >
                      {label}
                    </option>
                  );
                })}
              </select>
            </label>
          )}
        </>
      )}
      <div className={styles.postActions}>
        <button
          className={sharedStyles.primaryButton}
          disabled={busy}
          type="submit"
          data-ui="primaryButton"
        >
          저장
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={close}
        >
          취소
        </button>
      </div>
    </form>
  );
}
