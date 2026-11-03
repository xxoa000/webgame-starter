/* 등록된 캐릭터의 신원과 삭제 조작을 표시한다. */
import type { Character } from "../../lib/types";
import { GENDER_LABELS } from "../../lib/stats";
import { DeleteCharacterDialog } from "./DeleteCharacterDialog";

type Props = {
  character: Character;
  canDelete: boolean;
  busy: boolean;
  remove: (id: number, name: string) => Promise<void>;
};

export function CharacterProfile({
  character,
  busy,
  remove,
  canDelete,
}: Props) {
  /* 등록된 캐릭터의 신원과 삭제 조작을 표시한다. */

  return (
    <>
      <span className="badge">등록된 피계약자</span>
      <h2>{character.name}</h2>
      <div className="muted">
        {GENDER_LABELS[character.gender]} ·{" "}
        {character.age == null ? "나이 미설정" : `${character.age}세`}
      </div>
      <div className="personnel-unit">
        소속 <strong>현장대응센터</strong>
      </div>
      <p className="bio">{character.bio || "등록된 인적 사항이 없습니다."}</p>
      <div className="profile-id">
        PERSONNEL #{String(character.id).padStart(4, "0")}
      </div>
      <div className="personality-tags">
        {character.personality.map((keyword) => {
          /* 입력값에 따른 표시나 상태 변경을 처리한다. */ return (
            <span key={keyword.id}>{keyword.name}</span>
          );
        })}
      </div>
      {canDelete && (
        <DeleteCharacterDialog
          character={character}
          disabled={busy}
          remove={remove}
        />
      )}
    </>
  );
}
