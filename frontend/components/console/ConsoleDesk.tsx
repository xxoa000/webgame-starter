/* 하나의 회색 외장 안에 메인/서브 화면과 물리 메뉴·인증 버튼을 배치한다. 로그인은 서브 화면에 표시한다. */
"use client";
import { useState, type ReactNode } from "react";
import { DeathRecord } from "../characters/DeathRecord";
import { AuthPanel } from "../auth/AuthPanel";
import { usePathname } from "next/navigation";
import { GameProvider, useGame } from "../../hooks/useGame";
import { ExplorationProvider } from "../../hooks/useExploration";
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
  const exploring = usePathname().startsWith("/explore");
  return (
    <div
      className={`workstation dual-workstation ${exploring ? "field-terminal" : "control-terminal"}`}
    >
      <div className="console-pair">
        <div className="monitor-chassis main-chassis">
          <div className="monitor-glass main-glass">
            <MainConsole ready={ready}>{children}</MainConsole>
          </div>
          <div className="chassis-controls main-controls">
            <HardwareNavigation />
            <span className="vent-slots" aria-hidden="true" />
            <span className="power-light" aria-hidden="true" />
            <span className="power-label" aria-hidden="true">
              POWER
            </span>
          </div>
        </div>
        <aside
          className="monitor-chassis sub-chassis"
          aria-label="피계약자 서브콘솔"
        >
          <div className="monitor-glass sub-glass">
            <div className="sub-console-title">PERSONNEL / SUB CONSOLE</div>
            <div className="sub-console-content">
              {authOpen && !game.account ? (
                <section className="console-auth" aria-label="주무관 인증">
                  <AuthPanel
                    busy={game.busy}
                    run={game.run}
                    notify={game.setNotice}
                    login={async (username, password) => {
                      /* 비동기 요청 결과를 처리한다. */
                      await game.login(username, password);
                      setAuthOpen(false);
                    }}
                  />
                  {game.notice && (
                    <p className="notice" role="status">
                      {game.notice}
                    </p>
                  )}
                </section>
              ) : ready ? (
                <ContractorConsole />
              ) : game.account?.character?.status === "dead" ? (
                <DeathRecord />
              ) : (
                <div className="console-standby">
                  <span className="mini">PERSONNEL LINK</span>
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
          <div className="chassis-controls sub-controls">
            <span className="power-label" aria-hidden="true">
              PERSONNEL TERMINAL
            </span>
            <button
              type="button"
              className={`hardware-auth ${game.account || authOpen ? "is-active" : ""}`}
              disabled={game.busy || game.loading}
              aria-expanded={!game.account ? authOpen : undefined}
              aria-label={game.account ? "로그아웃" : "로그인 및 회원가입"}
              onClick={() => {
                /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */
                if (game.account) {
                  void game.run(game.logout);
                } else {
                  game.setNotice("");
                  setAuthOpen(!authOpen);
                }
              }}
            >
              <span className="hardware-label">
                {game.account ? "로그아웃" : "로그인"}
              </span>
              <span className="hardware-button" aria-hidden="true">
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
  return character?.status === "ready" ? (
    <ExplorationProvider key={character.id}>
      <ConsoleFrame ready>{children}</ConsoleFrame>
    </ExplorationProvider>
  ) : (
    <ConsoleFrame ready={false}>{children}</ConsoleFrame>
  );
}
export function ConsoleDesk({ children }: { children: ReactNode }) {
  /* 공유 계정 상태와 메인·서브 콘솔을 제공한다. */

  return (
    <GameProvider>
      <ConnectedDesk>{children}</ConnectedDesk>
    </GameProvider>
  );
}
