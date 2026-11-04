/* 모든 페이지에서 피계약자의 프로필·자원·기본 스탯·인벤토리·도감을 제공하는 서브콘솔. */
"use client";

import styles from "./Console.module.css";
import { classNames } from "../../lib/classNames";
import { PixelCharacter } from "../appearance/PixelCharacter";
import { useGame } from "../../hooks/useGame";
import { useExploration } from "../../hooks/useExploration";
import { ResourceBars } from "../characters/ResourceBars";
import Link from "next/link";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { SubEquipment } from "./SubEquipment";
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

  const pathname = usePathname();
  const account = useGame();
  const game = useExploration();
  const character = account.account?.character;
  const latestEvent = game.state?.history.at(-1);
  const thought = latestEvent?.scripts?.find((row) => row.layer === "THOUGHT");
  const eventKey = `${game.state?.id}:${latestEvent?.event_key ?? game.state?.version}`;
  const [visibleThought, setVisibleThought] = useState(false);
  useEffect(() => {
    /* 새 이벤트의 속마음을 잠시 표시하고 다음 이벤트나 로그아웃 시 정리한다. */
    setVisibleThought(pathname.startsWith("/explore") && Boolean(thought));
    const timer = setTimeout(() => setVisibleThought(false), 10000);
    return () => clearTimeout(timer);
  }, [eventKey, thought?.content]);
  useEffect(() => {
    /* 페이지를 이동하면 이전 이벤트의 속마음을 재생하지 않는다. */
    setVisibleThought(false);
  }, [pathname]);
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
      <Link
        href="/character"
        className={styles.explorerMiniProfile}
        aria-label={`${character.name}의 프로필 상세 보기`}
      >
        <div className={styles.portraitFrame}>
          {visibleThought && thought && (
            <div className={styles.thoughtBubble} role="status">
              {thought.content}
              <span
                className={classNames(
                  styles.thoughtDot,
                  styles.largeThoughtDot,
                )}
                aria-hidden="true"
              />
              <span
                className={classNames(
                  styles.thoughtDot,
                  styles.smallThoughtDot,
                )}
                aria-hidden="true"
              />
            </div>
          )}
          <PixelCharacter appearance={character.appearance} compact />
        </div>
        <strong>{character.name}</strong>
        <span>
          {GENDER_LABELS[character.gender]} · {character.age ?? "—"}세
        </span>
      </Link>
      <SubEquipment>
        <ResourceBars vitals={vitals} compact />
      </SubEquipment>
      <dl className={styles.statList}>
        {stats.map(([key, label]) => {
          return (
            <div key={key}>
              <dt>{label}</dt>
              <dd>{character.stats[key]}</dd>
            </div>
          );
        })}
      </dl>
    </>
  );
}
