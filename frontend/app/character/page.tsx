/* 피계약자 등록·프로필·능력치를 관리하는 전용 페이지. */
"use client";

import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "../../components/characters/Characters.module.css";
import { classNames } from "../../lib/classNames";
import { useState } from "react";
import { DeathRecord } from "../../components/characters/DeathRecord";
import { PersonalitySetup } from "../../components/personality/PersonalitySetup";
import { CharacterIdentityEditor } from "../../components/characters/CharacterIdentityEditor";
import { useGame } from "../../hooks/useGame";
import { AppShell } from "../../components/layout/AppShell";
import { CharacterForm } from "../../components/characters/CharacterForm";
import { CharacterProfile } from "../../components/characters/CharacterProfile";
import { CharacterCustomization } from "../../components/appearance/CharacterCustomization";
import { PixelCharacter } from "../../components/appearance/PixelCharacter";
import { StatsPanel } from "../../components/characters/StatsPanel";

// Page composes feature components; it does not contain form/API implementation.
export default function CharacterPage() {
  /* 피계약자의 등록·프로필·능력치 화면을 구성한다. */

  const [editing, setEditing] = useState(false);
  const game = useGame();
  const character = game.account?.character;
  return (
    <AppShell
      username={game.account?.username}
      ready={character?.status === "ready"}
      auth={game}
    >
      {game.loading ? (
        <div className={sharedStyles.panel} data-ui="panel">
          계정을 확인하는 중…
        </div>
      ) : !game.account ? (
        <section
          className={classNames(sharedStyles.panel, sharedStyles.empty)}
          data-ui="panel"
        >
          <h2>주무관 인증이 필요합니다.</h2>
          <p>오른쪽 하단의 인증 버튼으로 접속하십시오.</p>
        </section>
      ) : (
        <>
          <div className={styles.sectionBar}>
            <span>
              CONTRACTOR / 피계약자 <small> / 현장대응센터</small>
            </span>
          </div>
          {character?.status === "dead" ? (
            <DeathRecord />
          ) : !character ? (
            <section
              className={classNames(sharedStyles.panel, sharedStyles.empty)}
              data-ui="panel"
            >
              <div className={styles.emptyIcon}>✧</div>
              <h2>신규 피계약자를 등록하십시오.</h2>
              <p>
                초기 능력을 확인한 뒤 민간인 피계약자를 등록합니다. 능력
                재추첨은 추가 10회까지 가능합니다.
              </p>
              <button
                className={sharedStyles.primaryButton}
                disabled={game.busy}
                onClick={() => {
                  return void game.run(game.startCharacter);
                }}
                data-ui="primaryButton"
              >
                피계약자 등록 시작 →
              </button>
            </section>
          ) : (
            <div className={styles.characterGrid}>
              <section
                className={classNames(sharedStyles.panel, styles.profile)}
                data-ui="panel"
              >
                <div className={sharedStyles.smallLabel} data-ui="smallLabel">
                  {character.status === "ready"
                    ? "PERSONNEL RECORD / 신원 기록"
                    : "01 / 신원 등록"}
                </div>
                {character.status === "ready" && (
                  <div>
                    <PixelCharacter appearance={character.appearance} />
                  </div>
                )}
                {character.status === "ready" ? (
                  <CharacterProfile
                    character={character}
                    editing={editing}
                    onEdit={() => setEditing(!editing)}
                    canDelete={game.account?.auth === 9}
                    busy={game.busy}
                    remove={game.deleteCharacter}
                  />
                ) : (
                  <CharacterForm
                    key={character.id}
                    busy={game.busy}
                    run={game.run}
                    notify={game.setNotice}
                    finalize={game.finalize}
                  />
                )}
              </section>
              <StatsPanel
                character={character}
                ranges={game.ranges}
                busy={game.busy}
                reroll={() => {
                  return void game.run(game.reroll);
                }}
              />
            </div>
          )}
        </>
      )}
      {character?.status === "ready" && character.personality.length !== 3 && (
        <PersonalitySetup />
      )}
      {character?.status === "ready" && editing && (
        <CharacterIdentityEditor character={character} />
      )}
      {character?.status === "ready" && editing && (
        <CharacterCustomization
          key={character.id}
          character={character}
          busy={game.busy}
          run={game.run}
          save={game.saveAppearance}
        />
      )}
      {game.notice && (
        <div role="status" className={sharedStyles.message} data-ui="message">
          {game.notice}
        </div>
      )}
    </AppShell>
  );
}
