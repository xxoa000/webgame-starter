/* 전투·확정 도망·회복 물자 사용을 턴 선택지로 표시한다. */
"use client";
import { useState } from "react";
import { useExploration } from "../../hooks/useExploration";
export function CombatPanel({
  disabled,
  outsideCombat = false,
}: {
  disabled: boolean;
  outsideCombat?: boolean;
}) {
  /* 화면 상태를 확인하고 CombatPanel 기능을 실행한다. */

  const game = useExploration();
  const [itemsOpen, setItemsOpen] = useState(false);
  const monster = game.state?.combat;
  const items =
    game.inventory?.items.filter((item) => {
      /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return item.usable;
    }) ?? [];
  return (
    <section
      className="combat-panel"
      aria-label={outsideCombat ? "회복 아이템" : "전투"}
    >
      {monster && (
        <>
          <h2>{monster.name}</h2>
          <p>{monster.description}</p>
          <div className="combat-hp">
            <span>
              HP {monster.hp} / {monster.max_hp}
            </span>
            <progress
              value={monster.hp}
              max={monster.max_hp}
              aria-label="몬스터 HP"
            />
          </div>
        </>
      )}
      <div className="exploration-actions">
        {!outsideCombat && (
          <>
            <button
              className="primary"
              disabled={disabled}
              onClick={() => {
                /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

                setItemsOpen(false);
                void game.act("fight");
              }}
            >
              전투
            </button>
            <button
              disabled={disabled}
              onClick={() => {
                /* 화면 변화나 사용자 선택에 따른 처리를 실행한다. */

                setItemsOpen(false);
                void game.act("flee");
              }}
            >
              도망
            </button>
          </>
        )}
        <button
          disabled={disabled}
          aria-expanded={itemsOpen}
          onClick={() => {
            /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setItemsOpen(
              !itemsOpen,
            );
          }}
        >
          아이템
        </button>
      </div>
      {itemsOpen && (
        <div className="combat-items">
          {items.length ? (
            items.map((item) => {
              /* 각 항목의 화면 요소를 반환한다. */ return (
                <button
                  key={item.item_id}
                  disabled={disabled}
                  onClick={() => {
                    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return void game.act(
                      "use_item",
                      item.item_id,
                    );
                  }}
                >
                  {item.name} ×{item.quantity}
                </button>
              );
            })
          ) : (
            <p>사용 가능한 아이템 없음</p>
          )}
        </div>
      )}
    </section>
  );
}
