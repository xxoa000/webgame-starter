import type { Character, StatRanges } from "../../lib/types";
import { GENDER_LABELS } from "../../lib/stats";
import { StatsPanel } from "../characters/StatsPanel";

type Props = { character: Character; ranges: StatRanges };

export function ExplorerProfile({ character, ranges }: Props) {
  return (
    <div className="explorer-profile-detail">
      <div className="explorer-profile-identity">
        <div className="explorer-avatar">✦</div>
        <div>
          <h2>{character.name}</h2>
          <p>
            {GENDER_LABELS[character.gender]} ·{" "}
            {character.age == null ? "나이 미설정" : `${character.age}세`} ·{" "}
            {character.stats.height_cm} cm
          </p>
        </div>
      </div>
      {character.bio && <p className="explorer-bio">{character.bio}</p>}
      <StatsPanel
        character={character}
        ranges={ranges}
        busy={false}
        reroll={() => {}}
      />
    </div>
  );
}
