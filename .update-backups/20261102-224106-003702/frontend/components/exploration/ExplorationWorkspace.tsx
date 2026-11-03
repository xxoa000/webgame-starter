"use client";
import { useEffect, useState } from "react";
import { useExploration } from "../../hooks/useExploration";
import type { Character, StatRanges } from "../../lib/types";
import { kilograms } from "../../lib/exploration";
import { Subwindow } from "./Subwindow";
import { ExplorerProfile } from "./ExplorerProfile";
import { InventoryPanel } from "../inventory/InventoryPanel";

type Props = { character: Character; ranges: StatRanges };

export function ExplorationWorkspace({ character, ranges }: Props) {
  const game = useExploration();
  const [selectedMap, setSelectedMap] = useState(1);
  const [window, setWindow] = useState<"inventory" | "profile" | null>(null);
  const active = game.state?.status === "active";
  const pending = game.state?.pending_item;
  const selected = game.maps.find(
    (map) => map.id === (active ? game.state?.map_id : selectedMap),
  );
  const blocked = game.busy || window !== null;
  const latest = game.state?.history.at(-1);
  useEffect(() => {
    if (game.state) setSelectedMap(game.state.map_id);
  }, [game.state?.map_id]);

  if (game.loading)
    return <div className="panel">숲과 인벤토리를 불러오는 중…</div>;
  return (
    <div className="explore-page">
      <div className="explore-main-column">
        <div className="explore-section-title">
          <span>FIELD EXPLORATION</span>
          <span className="field-state">
            {window ? "일시정지" : active ? "탐색 중" : "탐색 대기"}
          </span>
        </div>
        <section className="forest-scene">
          <div className="forest-mist" aria-hidden="true" />
          <div className="forest-trees" aria-hidden="true">
            ♧
          </div>
          <div className="forest-caption">
            <div className="eyebrow">THE FOREST REMEMBERS</div>
            <h2>{selected?.name ?? "깊은 숲"}</h2>
            <p>
              {selected?.description ?? "마나를 품은 아이들이 살아가는 숲."}
            </p>
          </div>
          <span className="turn-counter">
            TURN{" "}
            <strong>{String(game.state?.turn ?? 0).padStart(2, "0")}</strong>
          </span>
        </section>
        {!active ? (
          <section className="panel exploration-start">
            <h2>
              {game.state?.status === "ended"
                ? "잠시 숲을 떠났어."
                : "오늘은 어디로 갈까?"}
            </h2>
            <p>
              {game.state?.status === "ended"
                ? "챙겨온 아이템은 그대로야. 새로운 탐색을 시작할 수 있어."
                : "버려진 아이에게 숲은 집이자 배움의 장소야. 작은 발견부터 시작해."}
            </p>
            <label>
              탐색 지역
              <select
                value={selectedMap}
                disabled={blocked}
                onChange={(event) => setSelectedMap(Number(event.target.value))}
              >
                {game.maps.map((map) => (
                  <option key={map.id} value={map.id}>
                    {map.name}
                  </option>
                ))}
              </select>
            </label>
            <div className="map-loot-preview">
              <span>
                빈손 {Math.round((selected?.empty_probability ?? 0) * 100)}%
              </span>
              {selected?.items.map((item) => (
                <span key={item.item_id}>
                  {item.name} {Math.round(item.probability * 100)}%
                </span>
              ))}
            </div>
            <button
              className="primary"
              disabled={blocked || !selected}
              onClick={() => void game.start(selectedMap)}
            >
              숲으로 들어가기 →
            </button>
          </section>
        ) : (
          <section className="panel exploration-turn" aria-live="polite">
            <div className="mini">
              {pending ? "SOMETHING FOUND" : "YOUR NEXT STEP"}
            </div>
            <h2>
              {pending
                ? "작은 발견."
                : latest?.kind === "rest"
                  ? "잠깐의 고요."
                  : latest?.kind === "empty"
                    ? "숲은 아직 조용해."
                    : "다음 걸음을 골라."}
            </h2>
            <p className="turn-message">{latest?.message}</p>
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
                  onClick={() => void game.act("take")}
                >
                  아이템을 가져간다
                </button>
                <button
                  disabled={blocked}
                  onClick={() => void game.act("give_up")}
                >
                  포기한다
                </button>
              </div>
            )}
            <div className="exploration-actions">
              <button
                className="primary"
                disabled={blocked || !!pending}
                onClick={() => void game.act("search")}
              >
                ⌕ 탐색
              </button>
              <button
                disabled={blocked || !!pending}
                onClick={() => void game.act("rest")}
              >
                ☾ 휴식
              </button>
              <button disabled={blocked} onClick={() => void game.act("end")}>
                {pending ? "발견을 포기하고 종료" : "탐색 종료"}
              </button>
            </div>
            <p className="hint">
              {pending
                ? "가져가거나 포기하면 다음 턴을 진행할 수 있어."
                : "선택할 때만 턴이 진행돼. 휴식은 현재 숨을 고르는 행동이며 능력치는 바꾸지 않아."}
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
            <div className="mini">FOREST JOURNAL / 최근 기록</div>
            <ol>
              {[...game.state.history].reverse().map((event, index) => (
                <li key={`${game.state?.id}-${index}`}>
                  <span>{String(event.turn).padStart(2, "0")}</span>
                  <p>{event.message}</p>
                </li>
              ))}
            </ol>
          </section>
        )}
      </div>
      <div className="explore-side-column">
        <div className="mini">YOUR COMPANION</div>
        <button
          className="explorer-mini-profile"
          disabled={game.busy}
          onClick={() => setWindow("profile")}
          aria-label={`${character.name}의 프로필 상세 보기`}
        >
          <div className="explorer-avatar">✦</div>
          <strong>{character.name}</strong>
          <span>
            {character.age == null ? "나이 미설정" : `${character.age}세`} ·
            마나를 품은 아이
          </span>
          <small>프로필 자세히 보기 ↗</small>
        </button>
        <button
          className="explorer-inventory-button"
          disabled={game.busy}
          onClick={() => setWindow("inventory")}
        >
          <span>▣ 인벤토리</span>
          <strong>
            {game.inventory?.used_slots ?? 0} /{" "}
            {game.inventory?.slot_capacity ?? 10}
          </strong>
        </button>
        <div className="explorer-weight">
          {kilograms(game.inventory?.current_weight_grams ?? 0)} /{" "}
          {kilograms(game.inventory?.max_weight_grams ?? 30000)} kg
        </div>
        <p className="hint">
          프로필과 인벤토리를 열어도
          <br />
          탐색은 종료되지 않아.
        </p>
      </div>
      {window && (
        <Subwindow
          title={window === "inventory" ? "나의 인벤토리" : "캐릭터 프로필"}
          kind={window}
          close={() => setWindow(null)}
        >
          {window === "inventory" ? (
            <InventoryPanel inventory={game.inventory} />
          ) : (
            <ExplorerProfile character={character} ranges={ranges} />
          )}
        </Subwindow>
      )}
    </div>
  );
}
