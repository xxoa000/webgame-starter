/* 게시글 요청·응답과 상태 표시 타입을 정의한다. */
export type PostStatus = 0 | 1 | 2 | 3;
export type Post = {
  id: number;
  title: string;
  content: string;
  username: string;
  is_notice: 0 | 1;
  post_status: PostStatus;
  create_at: string;
  update_at: string;
};
export type PostPage = {
  items: Post[];
  total: number;
  page: number;
  page_size: number;
};
export type PostInput = {
  title: string;
  content: string;
  is_notice?: 0 | 1;
  post_status?: PostStatus;
};
export const POST_STATUSES: Record<PostStatus, string> = {
  0: "숨김",
  1: "활성",
  2: "제재",
  3: "삭제",
};
export function postDate(value: string): string {
  /* 서버의 UTC 시각을 사용자의 지역 시간으로 표시한다. */
  return new Date(
    /[Zz]|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`,
  ).toLocaleString("ko-KR");
}
