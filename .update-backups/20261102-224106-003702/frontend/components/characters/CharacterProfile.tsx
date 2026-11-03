import type { Character } from "../../lib/types";
import { GENDER_LABELS } from "../../lib/stats";
import { DeleteCharacterDialog } from "./DeleteCharacterDialog";

type Props = {
  character: Character;
  busy: boolean;
  remove: (id: number, name: string) => Promise<void>;
};

export function CharacterProfile({ character, busy, remove }: Props) {
  return (
    <>
      <span className="badge">생성 완료</span>
      <h2>{character.name}</h2>
      <div className="muted">
        {GENDER_LABELS[character.gender]} ·{" "}
        {character.age == null ? "나이 미설정" : `${character.age}세`} ·{" "}
        {character.stats.height_cm} cm
      </div>
      <p className="bio">{character.bio || "아직 소개가 없어."}</p>
      <div className="profile-id">
        ARCHIVE #{String(character.id).padStart(4, "0")}
      </div>
      <DeleteCharacterDialog
        character={character}
        disabled={busy}
        remove={remove}
      />
    </>
  );
}
