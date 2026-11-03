/* 탐색 중인 캐릭터의 프로필과 자원을 표시한다. */
import type { Character, StatRanges } from "../../lib/types";
import { GENDER_LABELS } from "../../lib/stats";
import { StatsPanel } from "../characters/StatsPanel";

type Props = { character: Character; ranges: StatRanges };

export function ExplorerProfile({ character, ranges }: Props) {
  /* 탐색 중인 캐릭터의 프로필과 자원을 표시한다. */

  return (
    <div className="explorer-profile-detail">
      <div className="explorer-profile-identity">
        <div className="explorer-avatar">ID</div>
        <div>
          <h2>{character.name}</h2>
          <p>
            {GENDER_LABELS[character.gender]} ·{" "}
            {character.age == null ? "나이 미설정" : `${character.age}세`}
          </p>
        </div>
      </div>
      {character.bio && <p className="explorer-bio">{character.bio}</p>}
      <StatsPanel
        character={character}
        ranges={ranges}
        busy={false}
        reroll={() => {
          /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
        }}
      />
    </div>
  );
}
