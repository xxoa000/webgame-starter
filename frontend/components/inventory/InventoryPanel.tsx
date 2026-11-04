/* 소형 가로 수납칸으로 인벤토리를 표시한다. 칸을 선택하면 같은 패널 안에서 물품 정보를 확인한다. */
"use client";

import { ItemIndicators, itemFrame } from "../items/ItemIndicators";
import styles from "../exploration/Exploration.module.css";
import { classNames } from "../../lib/classNames";
import { useExploration } from "../../hooks/useExploration";
import { useGame } from "../../hooks/useGame";
import { useState } from "react";
import type { InventoryData } from "../../lib/exploration";
import { kilograms } from "../../lib/exploration";
export function InventoryPanel({
  inventory,
}: {
  inventory: InventoryData | null;
}) {
  /* 인벤토리 칸과 선택한 소지품의 정보를 표시한다. */

  const game = useExploration();
  const account = useGame();
  const [quantity, setQuantity] = useState(1);
  const disabled =
    game.busy || account.account?.character?.downed || game.state?.downed;
  const [selectedId, setSelectedId] = useState<number | null>(null);
  if (!inventory)
    return <p className={styles.trayMessage}>인벤토리를 불러오는 중…</p>;
  const selected = inventory.items.find((item) => {
    return item.item_id === selectedId;
  });
  return (
    <div className={styles.compactInventory}>
      <div className={styles.traySummary}>
        <span>
          수납 {inventory.used_slots}/{inventory.slot_capacity}
        </span>
        <span>
          {kilograms(inventory.current_weight_grams)} /{" "}
          {kilograms(inventory.max_weight_grams)} kg
        </span>
      </div>
      <div className={styles.storageLayout}>
        <div className={styles.storageCells} aria-label="보관 물품">
          {inventory.items.map((item) => {
            return (
              <button
                key={item.item_id}
                className={classNames(
                  styles.itemSlot,
                  itemFrame(item.rarity),
                  selectedId === item.item_id ? "" : "",
                )}
                aria-pressed={selectedId === item.item_id}
                aria-label={`${item.name}, ${item.quantity}개`}
                title={`${item.name} · ${item.quantity}개`}
                onClick={() => {
                  setQuantity(1);
                  return setSelectedId(item.item_id);
                }}
                data-ui={selectedId === item.item_id ? "selected" : ""}
              >
                <ItemIndicators rarity={item.rarity} edible={item.edible} />
                <span className={styles.storageIcon} aria-hidden="true">
                  {item.kind === "farming" ? "❋" : "◇"}
                </span>
                <span className={styles.storageName}>{item.name}</span>
                <span className={styles.storageCount}>×{item.quantity}</span>
              </button>
            );
          })}
          {Array.from(
            {
              length: Math.min(
                24,
                Math.max(0, inventory.slot_capacity - inventory.used_slots),
              ),
            },
            (_, index) => {
              return (
                <div
                  className={classNames(styles.itemSlot, styles.emptyCell)}
                  key={index}
                  aria-label="빈 수납칸"
                >
                  <span aria-hidden="true">·</span>
                </div>
              );
            },
          )}
        </div>
        <div className={styles.storageInspector} role="status">
          {selected ? (
            <>
              <strong>{selected.name}</strong>
              <span>
                ×{selected.quantity} · {kilograms(selected.total_weight_grams)}{" "}
                kg
              </span>
              <p>{selected.description}</p>
              <div className={styles.itemEffects}>
                {selected.hp_restore > 0 && (
                  <span>HP +{selected.hp_restore}</span>
                )}
                {selected.mp_restore > 0 && (
                  <span>MP +{selected.mp_restore}</span>
                )}
              </div>
              {selected.usable && (
                <button
                  disabled={disabled}
                  onClick={() => {
                    /* 회복 물자를 턴 소모 없이 사용한다. */ void game.inventoryAction(
                      "use",
                      selected.item_id,
                    );
                  }}
                >
                  사용
                </button>
              )}
              <label className={styles.discardQuantity}>
                수량{" "}
                <input
                  type="number"
                  min={1}
                  max={selected.quantity}
                  value={quantity}
                  onChange={(event) => {
                    /* 버릴 수량을 정수로 선택한다. */ setQuantity(
                      Math.max(
                        1,
                        Math.min(
                          selected.quantity,
                          Number(event.target.value) || 1,
                        ),
                      ),
                    );
                  }}
                />
              </label>
              <button
                disabled={disabled || quantity > selected.quantity}
                onClick={() => {
                  /* 확인 후 선택 수량의 물품을 버린다. */ if (
                    globalThis.confirm(
                      `${selected.name} ${quantity}개를 버릴까?`,
                    )
                  )
                    void game.inventoryAction(
                      "discard",
                      selected.item_id,
                      quantity,
                    );
                }}
              >
                버리기
              </button>
            </>
          ) : (
            <p>물품 칸을 선택하면 상세 정보가 표시됩니다.</p>
          )}
        </div>
      </div>
    </div>
  );
}
