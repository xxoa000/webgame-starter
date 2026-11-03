/* 인증 쿠키를 포함해 JSON API를 호출하고 실패 응답을 오류로 변환한다. */
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export async function api<T>(
  path: string,
  body?: unknown,
  method: "GET" | "POST" | "PATCH" | "DELETE" = body === undefined
    ? "GET"
    : "POST",
): Promise<T> {
  /* 호출자가 지정한 HTTP 메서드로 JSON 요청을 전송한다. */
  const response = await fetch(API_URL + path, {
    method,
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data: unknown = await response.json();
  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? data.detail
        : null;
    throw new Error(
      typeof detail === "string" ? detail : "입력 형식과 글자 수를 확인해.",
    );
  }
  return data as T;
}
