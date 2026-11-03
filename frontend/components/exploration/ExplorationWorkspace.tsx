/* 메인콘솔의 탐색 선택지와 현장 보고. 보조 창이 열린 동안 입력만 일시정지한다. */
"use client";
import { reportText } from "../../lib/world";
import { useEffect, useState } from "react";
import { useExploration } from "../../hooks/useExploration";
import type { Character, StatRanges } from "../../lib/types";
import { kilograms } from "../../lib/exploration";
import { ScriptLines } from "./ScriptLines";
import { CombatPanel } from "./CombatPanel";
import { MapLootPreview } from "./MapLootPreview";

type Props = { character: Character; ranges: StatRanges };

export function ExplorationWorkspace({ character, ranges }: Props) {
  /* 탐색 상태에 맞춰 맵과 행동 선택지를 표시한다. */

  const game = useExploration();
  const [selectedMap, setSelectedMap] = useState(1);
  const { window } = game;
  const stateVitals = game.state?.vitals;
  const vitals =
    stateVitals &&
    (!character.vitals ||
      Date.parse(stateVitals.server_time) >
        Date.parse(character.vitals.server_time))
      ? stateVitals
      : character.vitals;
  const active = game.state?.status === "active";
  const pending = game.state?.pending_item;
  const combat = game.state?.combat;
  const selected = game.maps.find((map) => {
    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
      map.id === (active ? game.state?.map_id : selectedMap)
    );
  });
  const blocked = game.busy || window !== null;
  const latest = game.state?.history.at(-1);
  useEffect(() => {
    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

    if (game.state) setSelectedMap(game.state.map_id);
  }, [game.state?.map_id]);
  useEffect(() => {
    /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

    if (
      !game.state &&
      game.maps.length &&
      !game.maps.some((map) => {
        /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
          map.id === selectedMap
        );
      })
    )
      setSelectedMap(game.maps[0].id);
  }, [game.maps, game.state, selectedMap]);

  if (game.loading)
    return <div className="panel">현장 데이터와 인벤토리를 수신하는 중…</div>;
  return (
    <div className="explore-page">
      <div className="explore-main-column">
        <div className="explore-section-title">
          <span>현장 영상 / FIELD OBSERVATION</span>
          <span className="field-state">
            {window ? "일시정지" : active ? "탐색 중" : "탐색 대기"}
          </span>
        </div>
        <section className="forest-scene">
          <div className="forest-mist" aria-hidden="true" />
          <div className="forest-trees" aria-hidden="true">
            ⟐
          </div>
          <div className="forest-caption">
            <div className="eyebrow">FRACTURE ZONE / 균열 내부</div>
            <h2>{selected?.name ?? "탐색 구역"}</h2>
            <p>{selected?.description}</p>
          </div>
          <span className="turn-counter">
            TURN{" "}
            <strong>{String(game.state?.turn ?? 0).padStart(2, "0")}</strong>
          </span>
        </section>
        <MapLootPreview map={selected} />
        {!!selected?.monsters?.length && (
          <div className="map-threats">
            {selected.monsters.map((monster) => {
              /* 각 항목의 화면 요소를 반환한다. */ return (
                <span key={monster.name}>
                  {monster.name} · {(monster.probability * 100).toFixed(1)}%
                </span>
              );
            })}
          </div>
        )}
        {!active ? (
          <section className="panel exploration-start">
            <h2>
              {game.state?.status === "ended"
                ? "현장 탐색이 종료되었습니다."
                : "탐색 구역을 지정하십시오."}
            </h2>
            <p>
              {game.state?.status === "ended"
                ? "회수 물품은 보관 중입니다. 새 탐색 구역을 지정할 수 있습니다."
                : "주무관은 중계 드론으로 선택지를 전달합니다. 피계약자의 자원 상태를 확인한 뒤 진입을 지시하십시오."}
            </p>
            <label>
              탐색 지역
              <select
                value={selectedMap}
                disabled={blocked}
                onChange={(event) => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setSelectedMap(
                    Number(event.target.value),
                  );
                }}
              >
                {game.maps.map((map) => {
                  /* 각 항목의 화면 요소를 반환한다. */ return (
                    <option key={map.id} value={map.id}>
                      {map.name}
                    </option>
                  );
                })}
              </select>
            </label>
            <button
              className="primary"
              disabled={blocked || !selected}
              onClick={() => {
                /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.start(
                  selectedMap,
                );
              }}
            >
              원격 탐색 개시 →
            </button>
          </section>
        ) : combat ? (
          <section className="panel exploration-turn">
            <p className="turn-message">{latest?.message}</p>
            <ScriptLines outputs={latest?.scripts} />
            <CombatPanel disabled={blocked} />
          </section>
        ) : (
          <section className="panel exploration-turn" aria-live="polite">
            <div className="mini">
              {pending ? "SOMETHING FOUND" : "YOUR NEXT STEP"}
            </div>
            <h2>
              {pending
                ? "회수 가능한 자원 발견"
                : latest?.kind === "rest"
                  ? "휴식 결과 보고"
                  : latest?.kind === "empty"
                    ? "탐색 결과: 자원 미발견"
                    : "다음 명령을 지정하십시오."}
            </h2>
            <p className="turn-message">
              {latest
                ? reportText(latest, game.state?.map_name ?? "")
                : "명령 대기 중"}
            </p>
            <ScriptLines outputs={latest?.scripts} />
            {pending && (
              <article className="discovered-item">
                <div className="item-symbol">❋</div>
                <div>
                  <h3>{pending.name}</h3>
                  <p>{pending.description}</p>
                  <small>
                    ×{pending.quantity} ·{" "}
                    {kilograms(pending.weight_grams * pending.quantity)} kg
                  </small>
                </div>
              </article>
            )}
            {pending && (
              <div className="discovery-actions">
                <button
                  className="primary"
                  disabled={blocked}
                  onClick={() => {
                    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.act(
                      "take",
                    );
                  }}
                >
                  아이템을 가져간다
                </button>
                <button
                  disabled={blocked}
                  onClick={() => {
                    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.act(
                      "give_up",
                    );
                  }}
                >
                  포기한다
                </button>
              </div>
            )}
            <div className="exploration-actions">
              <button
                className="primary"
                disabled={
                  blocked || !!pending || (vitals?.stamina_current ?? 0) < 1
                }
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.act(
                    "search",
                  );
                }}
              >
                ⌕ 탐색
              </button>
              <button
                disabled={blocked || !!pending}
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.act(
                    "rest",
                  );
                }}
              >
                ☾ 휴식
              </button>
              <button
                disabled={blocked}
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.act(
                    "end",
                  );
                }}
              >
                {pending ? "발견을 포기하고 종료" : "탐색 종료"}
              </button>
            </div>
            {!pending && <CombatPanel disabled={blocked} outsideCombat />}
            <p className="hint">
              {pending
                ? "가져가거나 포기하면 다음 턴을 진행할 수 있어."
                : "탐색당 스태미나 -1. 휴식은 HP·MP를 각각 5~30% 회복해. 스태미나는 5분마다 1씩 회복돼."}
            </p>
          </section>
        )}
        {game.error && (
          <div className="notice" role="alert">
            {game.error}
          </div>
        )}
        {game.state && (
          <section className="exploration-history">
            <div className="mini">OPERATION LOG / 현장 보고</div>
            <ol>
              {[...game.state.history].reverse().map((event, index) => {
                /* 각 항목의 화면 요소를 반환한다. */ return (
                  <li key={`${game.state?.id}-${index}`}>
                    <span>{String(event.turn).padStart(2, "0")}</span>
                    <div>
                      <p>{reportText(event, game.state?.map_name ?? "")}</p>
                      <ScriptLines outputs={event.scripts} />
                    </div>
                  </li>
                );
              })}
            </ol>
          </section>
        )}
      </div>
    </div>
  );
}
