/* 등록된 캐릭터의 신원과 삭제 조작을 표시한다. */
import styles from "./Characters.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import type { Character } from "../../lib/types";
import { GENDER_LABELS } from "../../lib/stats";
import { DeleteCharacterDialog } from "./DeleteCharacterDialog";
type Props = {
  character: Character;
  editing: boolean;
  onEdit: () => void;
  canDelete: boolean;
  busy: boolean;
  remove: (id: number, name: string) => Promise<void>;
};
export function CharacterProfile({
  character,
  busy,
  remove,
  canDelete,
  editing,
  onEdit,
}: Props) {
  /* 등록된 캐릭터의 신원과 삭제 조작을 표시한다. */

  return (
    <>
      <span className={styles.badge}>등록된 피계약자</span>
      <h2>{character.name}</h2>
      <div className={sharedStyles.mutedText} data-ui="mutedText">
        {GENDER_LABELS[character.gender]} ·{" "}
        {character.age == null ? "나이 미설정" : `${character.age}세`}
      </div>
      <div className={styles.personnelUnit}>
        소속 <strong>현장대응센터</strong>
      </div>
      <p className={styles.bio}>
        {character.bio || "등록된 인적 사항이 없습니다."}
      </p>
      <div className={styles.profileId}>
        PERSONNEL #{String(character.id).padStart(4, "0")}
      </div>
      <div className={styles.personalityTags}>
        {character.personality.map((keyword) => {
          return <span key={keyword.id}>{keyword.name}</span>;
        })}
      </div>
      <div
        className={
          canDelete ? styles.profileActions : styles.singleProfileAction
        }
      >
        <button onClick={onEdit} aria-expanded={editing}>
          {editing ? "수정 닫기" : "캐릭터 수정"}
        </button>
        {canDelete && (
          <DeleteCharacterDialog
            character={character}
            disabled={busy}
            remove={remove}
          />
        )}
      </div>
    </>
  );
}
