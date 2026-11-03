/* 모든 페이지에서 피계약자의 프로필·자원·기본 스탯·인벤토리·도감을 제공하는 서브콘솔. */
"use client";
import { PixelCharacter } from "../appearance/PixelCharacter";
import { useGame } from "../../hooks/useGame";
import { useExploration } from "../../hooks/useExploration";
import { ResourceBars } from "../characters/ResourceBars";
import { RelayDrone } from "../world/RelayDrone";
import Link from "next/link";
import { kilograms } from "../../lib/exploration";
import { GENDER_LABELS } from "../../lib/stats";
const stats = [
  ["strength", "근력"],
  ["stamina", "체력"],
  ["intelligence", "지능"],
  ["agility", "민첩"],
  ["luck", "행운"],
] as const;
export function ContractorConsole() {
  /* 피계약자 프로필과 자원을 서브 콘솔에 표시한다. */

  const account = useGame();
  const game = useExploration();
  const character = account.account?.character;
  if (!character || character.status !== "ready") return null;
  const current = game.state?.vitals;
  const vitals =
    current &&
    (!character.vitals ||
      Date.parse(current.server_time) >
        Date.parse(character.vitals.server_time))
      ? current
      : character.vitals;
  return (
    <>
      <div className="mini">CONTRACTOR / 피계약자</div>
      <Link
        href="/character"
        className="explorer-mini-profile"
        aria-label={`${character.name}의 프로필 상세 보기`}
      >
        <PixelCharacter appearance={character.appearance} compact />
        <strong>{character.name}</strong>
        <span>
          {GENDER_LABELS[character.gender]} · {character.age ?? "—"}세
        </span>
        <small>신원·능력 상세 ↗</small>
      </Link>
      <ResourceBars vitals={vitals} compact />
      <dl className="console-stat-list">
        {stats.map(([key, label]) => {
          /* 각 항목의 화면 요소를 반환한다. */ return (
            <div key={key}>
              <dt>{label}</dt>
              <dd>{character.stats[key]}</dd>
            </div>
          );
        })}
      </dl>
      <div className="inventory-tools">
        <button
          className="explorer-inventory-button"
          disabled={game.busy || game.loading}
          aria-expanded={game.window === "inventory"}
          onClick={() => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return game.setWindow(
              game.window === "inventory" ? null : "inventory",
            );
          }}
        >
          <span>인벤토리</span>
          <strong>
            {game.inventory?.used_slots ?? 0} /{" "}
            {game.inventory?.slot_capacity ?? 10}
          </strong>
        </button>
        <button
          className="encyclopedia-button"
          disabled={game.busy || game.loading}
          aria-expanded={game.window === "encyclopedia"}
          onClick={() => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return game.setWindow(
              game.window === "encyclopedia" ? null : "encyclopedia",
            );
          }}
        >
          도감
        </button>
      </div>
      <div className="explorer-weight">
        {kilograms(game.inventory?.current_weight_grams ?? 0)} /{" "}
        {kilograms(game.inventory?.max_weight_grams ?? 30000)} kg
      </div>
      <div className="relay-status">
        <RelayDrone />
        <div>
          <strong>주무관 중계 드론</strong>
          <small>현장대응센터 · 동행 유닛</small>
        </div>
      </div>
      {game.error && (
        <p className="hint" role="status">
          {game.error}
        </p>
      )}
    </>
  );
}
