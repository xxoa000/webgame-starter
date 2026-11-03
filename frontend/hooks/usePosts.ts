/* 게시판 조회·선택·작성·수정·소프트 삭제 상태를 관리한다. */
"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { Post, PostPage, PostInput } from "../lib/posts";
export function usePosts(canManage: boolean) {
  /* 페이지와 관리 모드에 맞는 게시글을 요청한다. */
  const [page, setPage] = useState(1);
  const [management, setManagement] = useState(false);
  const [data, setData] = useState<PostPage | null>(null);
  const [selected, setSelected] = useState<Post | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const pending = useRef(false);
  const sequence = useRef(0);
  const mounted = useRef(true);
  const reload = useCallback(async (): Promise<void> => {
    /* 오래된 목록 응답이 최신 페이지를 덮어쓰지 않게 한다. */
    const version = ++sequence.current;
    setLoading(true);
    try {
      const result = await api<PostPage>(
        `/posts?page=${page}&include_inactive=${management && canManage}`,
      );
      if (mounted.current && version === sequence.current) setData(result);
    } catch (error: unknown) {
      if (mounted.current)
        setError(error instanceof Error ? error.message : "목록 조회 실패");
    } finally {
      if (mounted.current && version === sequence.current) setLoading(false);
    }
  }, [page, management, canManage]);
  useEffect(() => {
    mounted.current = true;
    void reload();
    return () => {
      mounted.current = false;
      sequence.current++;
    };
  }, [reload]);
  useEffect(() => {
    if (!canManage) {
      setManagement(false);
      setSelected(null);
    }
  }, [canManage]);
  async function run(operation: () => Promise<void>): Promise<boolean> {
    /* 중복 변경 요청을 차단하고 실패 사유를 표시한다. */
    if (pending.current) return false;
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      await operation();
      return true;
    } catch (error: unknown) {
      if (mounted.current)
        setError(error instanceof Error ? error.message : "요청 실패");
      return false;
    } finally {
      pending.current = false;
      if (mounted.current) setBusy(false);
    }
  }
  async function open(id: number): Promise<void> {
    /* 상세 공개 상태를 서버에서 다시 검사한다. */
    await run(async () => {
      const post = await api<Post>(`/posts/${id}`);
      if (mounted.current) setSelected(post);
    });
  }
  async function save(input: PostInput, id?: number): Promise<boolean> {
    /* 작성 또는 수정을 수행하고 최신 목록으로 동기화한다. */
    return run(async () => {
      const post = await api<Post>(
        id ? `/posts/${id}` : "/posts",
        input,
        id ? "PATCH" : "POST",
      );
      if (mounted.current) setSelected(post);
      await reload();
    });
  }
  async function remove(id: number): Promise<void> {
    /* 삭제 상태로 바꾼 뒤 선택된 본문과 목록을 갱신한다. */
    await run(async () => {
      await api(`/posts/${id}`, undefined, "DELETE");
      if (mounted.current) setSelected(null);
      await reload();
    });
  }
  return {
    data,
    selected,
    setSelected,
    page,
    setPage,
    management,
    setManagement,
    error,
    busy,
    loading,
    open,
    save,
    remove,
  };
}
