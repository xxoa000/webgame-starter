/* 게시판 목록·상세와 사용자·운영자별 CRUD 조작을 구성한다. */
"use client";
import { useState } from "react";
import { useGame } from "../../hooks/useGame";
import { usePosts } from "../../hooks/usePosts";
import { PostEditor } from "./PostEditor";
import { POST_STATUSES, postDate, type Post } from "../../lib/posts";
export function PostBoard() {
  /* 계정 권한을 화면 표시 용도로만 사용하고 실제 인가는 서버에 맡긴다. */
  const game = useGame();
  const canManage = game.account?.auth === 1 || game.account?.auth === 9;
  const board = usePosts(canManage);
  const [editing, setEditing] = useState<Post | "new" | null>(null);
  const selected = board.selected;
  const own =
    selected?.username === game.account?.username &&
    selected?.is_notice === 0 &&
    selected?.post_status === 1;
  return (
    <div className="post-board">
      <div className="post-actions">
        <h2>게시판</h2>
        {game.account && (
          <button
            disabled={board.busy}
            onClick={() => {
              /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setEditing(
                "new",
              );
            }}
          >
            글 작성
          </button>
        )}
        {canManage && (
          <label className="post-checkbox">
            <input
              type="checkbox"
              checked={board.management}
              disabled={board.busy}
              onChange={(event) => {
                /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
                board.setManagement(event.target.checked);
                board.setPage(1);
                board.setSelected(null);
                setEditing(null);
              }}
            />
            운영 목록
          </label>
        )}
      </div>
      {board.error && (
        <p role="alert" className="notice">
          {board.error}
        </p>
      )}
      {editing !== null && game.account && (
        <PostEditor
          key={editing === "new" ? "new" : editing.id}
          post={editing === "new" ? undefined : editing}
          canManage={canManage}
          busy={board.busy}
          save={board.save}
          close={() => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setEditing(
              null,
            );
          }}
        />
      )}
      {board.loading ? (
        <p>불러오는 중…</p>
      ) : (
        <section className="panel post-list">
          {board.data?.items.length ? (
            board.data.items.map((post) => {
              /* 각 항목의 화면 요소를 반환한다. */ return (
                <button
                  key={post.id}
                  disabled={board.busy}
                  onClick={() => {
                    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
                    setEditing(null);
                    void board.open(post.id);
                  }}
                >
                  <span>
                    {post.is_notice === 1 ? "[공지] " : ""}
                    {post.title}
                  </span>
                  <small>
                    {post.username} · {postDate(post.create_at)}
                    {board.management
                      ? ` · ${POST_STATUSES[post.post_status]}`
                      : ""}
                  </small>
                </button>
              );
            })
          ) : (
            <p>등록된 글 없음</p>
          )}
        </section>
      )}
      <div className="post-actions">
        <button
          disabled={board.busy || board.loading || board.page <= 1}
          onClick={() => {
            /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
            board.setPage(board.page - 1);
            board.setSelected(null);
          }}
        >
          이전
        </button>
        <span>{board.page}</span>
        <button
          disabled={
            board.busy ||
            board.loading ||
            !board.data ||
            board.page * board.data.page_size >= board.data.total
          }
          onClick={() => {
            /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
            board.setPage(board.page + 1);
            board.setSelected(null);
          }}
        >
          다음
        </button>
      </div>
      {selected && editing === null && (
        <article className="panel">
          <h2>{selected.title}</h2>
          <small>
            {selected.username} · {postDate(selected.create_at)}
          </small>
          <div className="post-content">{selected.content}</div>
          {game.account && (canManage || own) && (
            <div className="post-actions">
              <button
                disabled={board.busy}
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setEditing(
                    selected,
                  );
                }}
              >
                수정
              </button>
              <button
                disabled={board.busy}
                onClick={() => {
                  /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
                  if (window.confirm("이 글을 삭제할까?"))
                    void board.remove(selected.id);
                }}
              >
                삭제
              </button>
            </div>
          )}
        </article>
      )}
    </div>
  );
}
