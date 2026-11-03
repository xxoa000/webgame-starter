/* 제목·본문과 운영자 전용 공지·상태 입력을 표시한다. */
"use client";
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
    const input: PostInput = { title, content };
    if (canManage) {
      input.is_notice = notice ? 1 : 0;
      if (post) input.post_status = status;
    }
    if (await save(input, post?.id)) close();
  }
  return (
    <form
      className="panel post-editor"
      onSubmit={(event) => {
        /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void submit(
          event,
        );
      }}
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
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setTitle(
              event.target.value,
            );
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
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setContent(
              event.target.value,
            );
          }}
        />
      </label>
      {canManage && (
        <>
          <label className="post-checkbox">
            <input
              type="checkbox"
              checked={notice}
              disabled={busy}
              onChange={(event) => {
                /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setNotice(
                  event.target.checked,
                );
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
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setStatus(
                    Number(event.target.value) as PostStatus,
                  );
                }}
              >
                {Object.entries(POST_STATUSES).map(([key, label]) => {
                  /* 각 항목의 화면 요소를 반환한다. */ return (
                    <option value={key} key={key}>
                      {label}
                    </option>
                  );
                })}
              </select>
            </label>
          )}
        </>
      )}
      <div className="post-actions">
        <button className="primary" disabled={busy} type="submit">
          저장
        </button>
        <button type="button" disabled={busy} onClick={close}>
          취소
        </button>
      </div>
    </form>
  );
}
