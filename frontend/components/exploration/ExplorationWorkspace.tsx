/* 탐색 지도와 행동 패널을 표시하고 모든 탐색 상태에서 드론을 유지한다. */
"use client";

import { ItemIndicators, itemFrame } from "../items/ItemIndicators";
import sharedStyles from "../../styles/shared/Controls.module.css";
import styles from "./Observation.module.css";
import { classNames } from "../../lib/classNames";
import { useEffect, useState } from "react";
import type { ChangeEvent } from "react";
import { useExploration } from "../../hooks/useExploration";
import { useMapPresence } from "../../hooks/useMapPresence";
import { kilograms } from "../../lib/exploration";
import type { ExplorationAction } from "../../lib/exploration";
import type { Character, StatRanges } from "../../lib/types";
import { pendingCombatDrop } from "../../lib/pendingCombatDrop";
import { reportText } from "../../lib/world";
import { RelayDrone } from "../world/RelayDrone";
import { CombatWindow } from "./CombatWindow";
import { DroneMap } from "./DroneMap";
import { MapLootPreview } from "./MapLootPreview";
import { RescueBoard } from "./RescueBoard";
import { RescuePanel } from "./RescuePanel";
import { ScriptLines } from "./ScriptLines";
import { RaidPanel } from "./RaidPanel";
type Props = {
  character: Character;
  ranges: StatRanges;
};
export function ExplorationWorkspace({ character }: Props) {
  /* 최신 탐색 상태를 기준으로 지도·결과·행동 버튼을 구성한다. */
  const game = useExploration();
  const [selectedMap, setSelectedMap] = useState(1);
  const { state, maps, window: equipmentWindow } = game;
  const stateMapId = state?.map_id;
  const active = state?.status === "active";
  const pending = state?.pending_item;
  const combat = state?.combat;
  const battleDrop = pendingCombatDrop(state);
  const battleWindowOpen = Boolean(
    active && !state?.downed && (combat || battleDrop),
  );
  const latest = state?.history.at(-1);
  const downed = state?.downed ?? character.downed;
  const paused = equipmentWindow !== null;
  const blocked = game.busy || paused || downed;
  const onlineCounts = useMapPresence(active, stateMapId);
  const stateVitals = state?.vitals;
  const characterVitals = character.vitals;
  const useStateVitals =
    stateVitals &&
    (!characterVitals ||
      Date.parse(stateVitals.server_time) >
        Date.parse(characterVitals.server_time));
  const vitals = useStateVitals ? stateVitals : characterVitals;
  const noStamina = (vitals?.stamina_current ?? 0) < 1;
  const actionBlocked = blocked || !!pending;
  const currentMapId = active ? stateMapId : selectedMap;
  const selected = maps.find((map) => map.id === currentMapId);
  const onlineCount =
    onlineCounts === null
      ? "—"
      : selected
        ? (onlineCounts[String(selected.id)] ?? 0)
        : 0;
  const mapTitle = active ? (selected?.name ?? "탐색 구역") : "균열 탐색";
  const mapDescription = active
    ? selected?.description
    : "드론을 통해 현장을 관측하고, 피계약자의 행동을 지시하세요.";
  const statusTitle = paused
    ? "일시정지"
    : downed
      ? "구조 대기"
      : active
        ? "탐색 중"
        : "탐색 대기";
  const resultTitle = pending
    ? "회수 가능한 자원 발견"
    : latest?.kind === "rest"
      ? "휴식 결과"
      : latest?.kind === "empty"
        ? "탐색 결과: 자원 미발견"
        : "";
  useEffect(() => {
    /* 서버의 탐색 지역이 바뀌면 지도 선택을 동기화한다. */
    if (active && stateMapId !== undefined) {
      setSelectedMap(stateMapId);
    }
  }, [active, stateMapId]);
  useEffect(() => {
    /* 최초 조회에서 유효한 탐색 지역을 선택한다. */
    if (
      !active &&
      maps.length > 0 &&
      !maps.some((map) => map.id === selectedMap)
    ) {
      setSelectedMap(maps[0].id);
    }
  }, [maps, active, selectedMap]);
  function handleMapChange(event: ChangeEvent<HTMLSelectElement>) {
    /* 지역 선택 값을 숫자 ID로 변환한다. */
    setSelectedMap(Number(event.target.value));
  }
  function handleStart() {
    /* 선택 지역에서 탐색을 시작한다. */
    void game.start(selectedMap);
  }
  function handleAction(action: ExplorationAction) {
    /* 턴과 자원 검증은 기존 탐색 API에 맡긴다. */
    void game.act(action);
  }
  function openInventory() {
    /* 서브 콘솔의 인벤토리를 연다. */
    game.setWindow(equipmentWindow === "inventory" ? null : "inventory");
  }
  if (game.loading) {
    return (
      <div className={sharedStyles.panel} data-ui="panel">
        현장 데이터를 수신받는 중…
      </div>
    );
  }
  return (
    <div className={styles.explorationPage}>
      <div className={styles.mainColumn}>
        {game.raid && (
          <RaidPanel
            raid={game.raid}
            canAttack={
              !!active &&
              stateMapId === game.raid.map_id &&
              !downed &&
              !paused &&
              !combat &&
              !pending
            }
            busy={game.busy}
            onAttack={() => void game.attackRaid()}
          />
        )}
        <div className={styles.observationDesk}>
          <div className={styles.observationSurface} inert={battleWindowOpen}>
            <header className={styles.observationHeader}>
              <div className={styles.mapHeading}>
                <h2>{mapTitle}</h2>
                <p>{mapDescription}</p>
              </div>
              <div className={styles.mapStatus}>
                <span className={styles.onlinePlayers}>
                  <i /> ONLINE {onlineCount}
                </span>
                <span className={styles.turnCount}>
                  TURN{" "}
                  <strong>{String(state?.turn ?? 0).padStart(2, "0")}</strong>
                </span>
              </div>
            </header>
            <section
              className={styles.mapViewport}
              aria-label="균열 탐색 관측 지도"
            >
              <DroneMap
                maps={maps}
                selected={selected}
                active={active}
                step={state?.position_step ?? 0}
                blocked={blocked}
                onSelect={setSelectedMap}
              />
              <div className={styles.droneScanlines} aria-hidden="true" />
              <div className={styles.droneScale} aria-hidden="true">
                100 m · N ↑
              </div>
            </section>
            <div className={styles.mapItemPanel}>
              <MapLootPreview map={selected} />
              {!!selected?.monsters?.length && (
                <div className={styles.droneThreats}>
                  {selected.monsters.map((monster) => (
                    <span key={monster.name}>
                      {monster.name} · {(monster.probability * 100).toFixed(1)}%
                    </span>
                  ))}
                </div>
              )}
            </div>
            <div className={styles.actionArea}>
              <header className={styles.actionHeader}>
                <div className={styles.explorationStatus}>
                  <h2>
                    {battleDrop
                      ? "전투 승리"
                      : combat
                        ? "전투 중"
                        : statusTitle}
                  </h2>
                  <span className={styles.droneLink}>
                    <i /> {active ? "LIVE" : "STANDBY"}
                  </span>
                </div>
                <div
                  className={classNames(
                    styles.droneInfo,
                    styles.companionDrone,
                  )}
                  data-ui="droneInfo companionDrone"
                >
                  <RelayDrone />
                  <div>
                    <strong>관제 드론</strong>
                    <small>현장대응센터 · 동행 유닛</small>
                  </div>
                </div>
              </header>
              {downed ? (
                <RescuePanel />
              ) : !active ? (
                <section
                  className={classNames(sharedStyles.panel, styles.startPanel)}
                  data-ui="panel"
                >
                  <p className={styles.selectedMapDescription}>
                    {selected?.description}
                  </p>

                  <label>
                    탐색 지역
                    <select
                      value={selectedMap}
                      disabled={blocked}
                      onChange={handleMapChange}
                    >
                      {maps.map((map) => (
                        <option key={map.id} value={map.id}>
                          {map.name}
                        </option>
                      ))}
                    </select>
                  </label>

                  <button
                    className={sharedStyles.primaryButton}
                    disabled={blocked || !selected}
                    onClick={handleStart}
                    data-ui="primaryButton"
                  >
                    원격 탐색 개시 →
                  </button>
                </section>
              ) : battleWindowOpen ? null : (
                <section
                  className={classNames(sharedStyles.panel, styles.actionPanel)}
                  aria-live="polite"
                  data-ui="panel"
                >
                  <div className={styles.resultColumn}>
                    {resultTitle && <h4>{resultTitle}</h4>}

                    <div className={styles.encounterLayout}>
                      <div>
                        <p className={styles.turnMessage}>
                          {latest
                            ? reportText(latest, state?.map_name ?? "")
                            : "명령 대기 중"}
                        </p>
                        <ScriptLines outputs={latest?.scripts} />
                      </div>

                      {pending && (
                        <article
                          className={classNames(
                            styles.discoveredItem,
                            itemFrame(pending.rarity),
                          )}
                        >
                          <ItemIndicators
                            rarity={pending.rarity}
                            edible={pending.edible}
                          />
                          <div className={styles.itemSymbol}>❋</div>
                          <div>
                            <h3>{pending.name}</h3>
                            <p>{pending.description}</p>
                            <small>
                              ×{pending.quantity} ·{" "}
                              {kilograms(
                                pending.weight_grams * pending.quantity,
                              )}{" "}
                              kg
                            </small>
                          </div>
                        </article>
                      )}
                    </div>
                  </div>
                  <div className={styles.commandColumn}>
                    <div className={styles.explorationActions}>
                      <button
                        className={sharedStyles.primaryButton}
                        disabled={
                          pending ? blocked : actionBlocked || noStamina
                        }
                        onClick={() =>
                          handleAction(pending ? "take" : "search")
                        }
                        data-ui="primaryButton"
                      >
                        {pending ? "회수" : "⌕ 탐색"}
                      </button>
                      <button
                        disabled={
                          pending ? blocked : actionBlocked || noStamina
                        }
                        onClick={() =>
                          handleAction(pending ? "give_up" : "rest")
                        }
                      >
                        {pending ? "포기" : "☾ 휴식"}
                      </button>
                      <button
                        disabled={game.busy || downed}
                        aria-expanded={equipmentWindow === "inventory"}
                        onClick={openInventory}
                      >
                        아이템
                      </button>
                    </div>

                    <div className={styles.explorationEndRow}>
                      <button
                        disabled={blocked}
                        onClick={() => handleAction("end")}
                      >
                        {pending ? "발견을 포기하고 종료" : "탐색 종료"}
                      </button>
                    </div>

                    <p className={sharedStyles.helpText} data-ui="helpText">
                      {pending
                        ? "가져가거나 포기하면 다음 턴을 진행할 수 있습니다."
                        : "탐색·휴식은 턴 1과 스태미나 1을 소비합니다. " +
                          "아이템 사용은 턴을 소비하지 않습니다."}
                    </p>
                  </div>
                </section>
              )}
            </div>
          </div>
          {battleWindowOpen && (
            <CombatWindow
              combat={combat ?? null}
              loot={battleDrop}
              disabled={blocked}
            />
          )}
        </div>
        {active && !downed && <RescueBoard />}

        {game.error && (
          <div className={sharedStyles.message} role="alert" data-ui="message">
            {game.error}
          </div>
        )}

        {state && (
          <section className={styles.explorationHistory}>
            <div className={sharedStyles.smallLabel} data-ui="smallLabel">
              OPERATION LOG / 현장 보고
            </div>
            <ol>
              {[...state.history].reverse().map((event, index) => (
                <li key={`${state.id}-${index}`}>
                  <span>{String(event.turn).padStart(2, "0")}</span>
                  <div>
                    <p>{reportText(event, state.map_name)}</p>
                    <ScriptLines outputs={event.scripts} />
                  </div>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
    </div>
  );
}
