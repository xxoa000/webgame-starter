"use client";
import { useRef, useState, type FormEvent } from "react";
import type { Character } from "../../lib/types";

type Props = {
  character: Character;
  disabled: boolean;
  remove: (id: number, name: string) => Promise<void>;
};

export function DeleteCharacterDialog({ character, disabled, remove }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const pending = useRef(false);
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (pending.current || name !== character.name) return;
    pending.current = true;
    setDeleting(true);
    setError("");
    try {
      await remove(character.id, name);
      dialog.current?.close();
    } catch (error) {
      setError(error instanceof Error ? error.message : "삭제에 실패했어.");
    } finally {
      pending.current = false;
      setDeleting(false);
    }
  }
  return (
    <>
      <button
        className="danger-outline"
        disabled={disabled}
        onClick={() => {
          setName("");
          setError("");
          dialog.current?.showModal();
        }}
      >
        캐릭터 삭제
      </button>
      <dialog
        ref={dialog}
        className="delete-dialog"
        aria-labelledby="delete-title"
        aria-describedby="delete-description"
        onCancel={(event) => {
          if (pending.current) event.preventDefault();
        }}
      >
        <form onSubmit={submit}>
          <div className="eyebrow">DELETE CHARACTER</div>
          <h2 id="delete-title">정말 캐릭터를 삭제할까?</h2>
          <p id="delete-description">
            프로필과 스탯이 삭제 이력으로 이동해. 삭제 후에는 이 화면에서 복구할
            수 없어.
          </p>
          <p>
            계속하려면 <strong>{character.name}</strong> 이름을 정확히 입력해.
          </p>
          <label>
            캐릭터 이름
            <input
              autoFocus
              required
              maxLength={24}
              autoComplete="off"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="삭제할 캐릭터 이름"
            />
          </label>
          {error && (
            <p role="alert" className="delete-error">
              {error}
            </p>
          )}
          <div className="dialog-actions">
            <button
              type="button"
              disabled={deleting}
              onClick={() => dialog.current?.close()}
            >
              취소
            </button>
            <button
              className="danger-solid"
              disabled={deleting || name !== character.name}
            >
              {deleting ? "삭제 중…" : "캐릭터 영구 삭제"}
            </button>
          </div>
        </form>
      </dialog>
    </>
  );
}
