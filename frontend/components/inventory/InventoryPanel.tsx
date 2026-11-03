/* 소형 가로 수납칸으로 인벤토리를 표시한다. 칸을 선택하면 같은 패널 안에서 물품 정보를 확인한다. */
"use client";
import { useState } from "react";
import type { InventoryData } from "../../lib/exploration";
import { kilograms } from "../../lib/exploration";
export function InventoryPanel({
  inventory,
}: {
  inventory: InventoryData | null;
}) {
  /* 인벤토리 칸과 선택한 소지품의 정보를 표시한다. */

  const [selectedId, setSelectedId] = useState<number | null>(null);
  if (!inventory)
    return <p className="tray-message">인벤토리를 불러오는 중…</p>;
  const selected = inventory.items.find((item) => {
    /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
      item.item_id === selectedId
    );
  });
  return (
    <div className="compact-inventory">
      <div className="tray-summary">
        <span>
          수납 {inventory.used_slots}/{inventory.slot_capacity}
        </span>
        <span>
          {kilograms(inventory.current_weight_grams)} /{" "}
          {kilograms(inventory.max_weight_grams)} kg
        </span>
      </div>
      <div className="storage-layout">
        <div className="storage-cells" aria-label="보관 물품">
          {inventory.items.map((item) => {
            /* 각 항목의 화면 요소를 반환한다. */ return (
              <button
                key={item.item_id}
                className={`storage-cell occupied ${selectedId === item.item_id ? "selected" : ""}`}
                aria-pressed={selectedId === item.item_id}
                aria-label={`${item.name}, ${item.quantity}개`}
                title={`${item.name} · ${item.quantity}개`}
                onClick={() => {
                  /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return setSelectedId(
                    item.item_id,
                  );
                }}
              >
                <span className="storage-icon" aria-hidden="true">
                  {item.kind === "farming" ? "❋" : "◇"}
                </span>
                <span className="storage-name">{item.name}</span>
                <span className="storage-count">×{item.quantity}</span>
              </button>
            );
          })}
          {Array.from(
            {
              length: Math.max(
                0,
                inventory.slot_capacity - inventory.used_slots,
              ),
            },
            (_, index) => {
              /* 입력값에 따른 상태 변경이나 반환값을 처리한다. */ return (
                <div
                  className="storage-cell empty-cell"
                  key={index}
                  aria-label="빈 수납칸"
                >
                  <span aria-hidden="true">·</span>
                </div>
              );
            },
          )}
        </div>
        <div className="storage-inspector" role="status">
          {selected ? (
            <>
              <strong>{selected.name}</strong>
              <span>
                ×{selected.quantity} · {kilograms(selected.total_weight_grams)}{" "}
                kg
              </span>
              <p>{selected.description}</p>
            </>
          ) : (
            <p>물품 칸을 선택하면 상세 정보가 표시됩니다.</p>
          )}
        </div>
      </div>
    </div>
  );
}
