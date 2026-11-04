/* 하나의 회색 외장 안에 메인/서브 화면과 물리 메뉴·인증 버튼을 배치한다. 로그인은 서브 화면에 표시한다. */
"use client";

import styles from "./Console.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useState, type ReactNode } from "react";
import { DeathRecord } from "../characters/DeathRecord";
import { AuthPanel } from "../auth/AuthPanel";
import { usePathname } from "next/navigation";
import { GameProvider, useGame } from "../../hooks/useGame";
import { ExplorationProvider } from "../../hooks/useExploration";
import { AudioProvider } from "../../hooks/useAudio";
import { HardwareNavigation } from "./HardwareNavigation";
import { ContractorConsole } from "./ContractorConsole";
import { MainConsole } from "./MainConsole";
function ConsoleFrame({
  children,
  ready,
}: {
  children: ReactNode;
  ready: boolean;
}) {
  /* 콘솔 화면과 하단 메뉴·인증 버튼을 배치한다. */

  const game = useGame();
  const [authOpen, setAuthOpen] = useState(false);
  const pathname = usePathname();
  const exploring = pathname.startsWith("/explore");
  useEffect(() => {
    /* 페이지에 남은 인증 입력과 알림을 초기화한다. */
    setAuthOpen(false);
    game.setNotice("");
  }, [pathname]);
  return (
    <div
      className={classNames(
        styles.workstation,
        styles.dualConsole,
        exploring ? styles.explorationTheme : "",
      )}
      data-ui={classNames("dualConsole", exploring ? "explorationTheme" : "")}
    >
      <div className={styles.consolePair}>
        <div className={classNames(styles.monitorFrame, styles.mainChassis)}>
          <div className={classNames(styles.monitorScreen, styles.mainGlass)}>
            <MainConsole ready={ready}>{children}</MainConsole>
          </div>
          <div
            className={classNames(styles.chassisControls, styles.mainControls)}
          >
            <HardwareNavigation />
            <span
              className={styles.ventSlots}
              aria-hidden="true"
            />
            <span
              className={styles.powerLight}
              aria-hidden="true"
            />
            <span
              className={styles.powerLabel}
              aria-hidden="true"
            >
              POWER
            </span>
          </div>
        </div>

        <aside
          className={classNames(styles.monitorFrame, styles.subChassis)}
          aria-label="서브콘솔"
        >
          <div className={classNames(styles.monitorScreen, styles.subGlass)}>
            <div
              key={pathname}
              className={styles.subConsoleContent}
              data-ui="subConsoleContent"
            >
              <header className={styles.subConsoleHeader}>
                PERSONNEL / SUB CONSOLE
              </header>
              {authOpen && !game.account ? (
                <section
                  className={styles.consoleAuth}
                  aria-label="주무관 인증"
                  data-ui="consoleAuth"
                >
                  <AuthPanel
                    busy={game.busy}
                    run={game.run}
                    notify={game.setNotice}
                    login={async (username, password) => {
                      /* 로그인이 완료된 후 서브 콘솔 인증 입력을 닫는다. */
                      await game.login(username, password);
                      setAuthOpen(false);
                    }}
                  />
                  {game.notice && (
                    <p
                      className={sharedStyles.message}
                      role="status"
                      data-ui="message"
                    >
                      {game.notice}
                    </p>
                  )}
                </section>
              ) : ready ? (
                <ContractorConsole />
              ) : game.account?.character?.status === "dead" ? (
                exploring ? (
                  <p
                    className={sharedStyles.message}
                    data-ui="message"
                  >
                    생체 신호 종료 · 메인 콘솔에서 사망 경위를 확인하십시오.
                  </p>
                ) : (
                  <DeathRecord />
                )
              ) : (
                <div className={styles.consoleStandby}>
                  <span
                    className={sharedStyles.smallLabel}
                    data-ui="smallLabel"
                  >
                    PERSONNEL LINK
                  </span>
                  <h2>
                    {game.loading
                      ? "신원 확인 중…"
                      : game.account
                        ? "피계약자 등록 대기"
                        : "주무관 인증 대기"}
                  </h2>
                  <p>
                    {game.account
                      ? "피계약자 등록을 완료하면 프로필과 능력치가 표시됩니다."
                      : "오른쪽 하단의 인증 버튼을 누르십시오."}
                  </p>
                </div>
              )}
            </div>
          </div>

          <div
            className={classNames(styles.chassisControls, styles.subControls)}
          >
            <span
              className={styles.powerLabel}
              aria-hidden="true"
            >
              PERSONNEL TERMINAL
            </span>
            <button
              type="button"
              className={classNames(
                styles.hardwareAuth,
                game.account || authOpen ? styles.isActive : "",
              )}
              disabled={game.busy || game.loading}
              aria-expanded={!game.account ? authOpen : undefined}
              aria-label={game.account ? "로그아웃" : "로그인 및 회원가입"}
              onClick={() => {
                if (game.account) {
                  void game.run(game.logout);
                } else {
                  game.setNotice("");
                  setAuthOpen(!authOpen);
                }
              }}
              data-ui={game.account || authOpen ? "" : ""}
            >
              <span className={styles.hardwareLabel}>
                {game.account ? "로그아웃" : "로그인"}
              </span>
              <span
                className={styles.hardwareButton}
                aria-hidden="true"
              >
                <span />
              </span>
            </button>
          </div>
        </aside>
      </div>
    </div>
  );
}
function ConnectedDesk({ children }: { children: ReactNode }) {
  /* 등록된 캐릭터에 탐색 공유 상태를 연결한다. */

  const game = useGame();
  const character = game.account?.character;
  return character && ["ready", "dead"].includes(character.status) ? (
    <ExplorationProvider key={character.id}>
      <ConsoleFrame ready={character.status === "ready"}>
        {children}
      </ConsoleFrame>
    </ExplorationProvider>
  ) : (
    <ConsoleFrame ready={false}>{children}</ConsoleFrame>
  );
}
export function ConsoleDesk({ children }: { children: ReactNode }) {
  /* 공유 계정 상태와 메인·서브 콘솔을 제공한다. */

  return (
    <AudioProvider>
      <GameProvider>
        <ConnectedDesk>{children}</ConnectedDesk>
      </GameProvider>
    </AudioProvider>
  );
}
