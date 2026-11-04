/* 탐색 중인 캐릭터의 프로필과 자원을 표시한다. */
import styles from "./Exploration.module.css";
import type { Character, StatRanges } from "../../lib/types";
import { GENDER_LABELS } from "../../lib/stats";
import { StatsPanel } from "../characters/StatsPanel";
type Props = {
  character: Character;
  ranges: StatRanges;
};
export function ExplorerProfile({ character, ranges }: Props) {
  /* 탐색 중인 캐릭터의 프로필과 자원을 표시한다. */

  return (
    <div>
      <div className={styles.explorerProfileIdentity}>
        <div className={styles.explorerAvatar}>ID</div>
        <div>
          <h2>{character.name}</h2>
          <p>
            {GENDER_LABELS[character.gender]} ·{" "}
            {character.age == null ? "나이 미설정" : `${character.age}세`}
          </p>
        </div>
      </div>

      {character.bio && <p className={styles.explorerBio}>{character.bio}</p>}

      <StatsPanel
        character={character}
        ranges={ranges}
        busy={false}
        reroll={() => {}}
      />
    </div>
  );
}
