/* 상점 NPC와 무료 크레딧 구매·판매 목록을 메인 콘솔에 표시한다. */
"use client";

import { ItemIndicators, itemFrame } from "../items/ItemIndicators";
import type { ItemTraits } from "../../lib/items";
import { classNames } from "../../lib/classNames";
import styles from "./Shop.module.css";
import sharedStyles from "../../styles/shared/Controls.module.css";
import { useEffect, useRef, useState } from "react";
import { api } from "../../lib/api";
import { useExploration } from "../../hooks/useExploration";
import { useGame } from "../../hooks/useGame";
import { kilograms } from "../../lib/exploration";
type Upgrade = {
  code: "bag_expansion" | "stat_point";
  name: string;
  description: string;
  price: number;
};
type Product = ItemTraits & {
  item_id: number;
  name: string;
  description: string;
  buy_price: number;
  sell_price: number;
  weight_grams: number;
};
export function ShopWorkspace() {
  /* 거래 가격과 잔액은 서버에서 검증하고 완료 후 서브 인벤토리를 갱신한다. */
  const game = useExploration();
  const account = useGame();
  const [upgrades, setUpgrades] = useState<Upgrade[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [mode, setMode] = useState<"buy" | "sell">("buy");
  const [quantity, setQuantity] = useState(1);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const pending = useRef(false);
  useEffect(() => {
    /* 실제 상점 상품 목록을 불러온다. */ let alive = true;
    api<Product[]>("/shop")
      .then((rows) => {
        if (alive) setProducts(rows);
      })
      .catch((error) => {
        if (alive)
          setNotice(error instanceof Error ? error.message : "상점 조회 실패");
      });
    return () => {
      alive = false;
    };
  }, []);
  useEffect(() => {
    /* 영구 상품의 가격은 DB에서 조회하고 반복 구매할 수 있다. */
    let alive = true;
    api<Upgrade[]>("/shop/upgrades")
      .then((rows) => {
        if (alive) setUpgrades(rows);
      })
      .catch((error) => {
        if (alive)
          setNotice(error instanceof Error ? error.message : "상품 조회 실패");
      });
    return () => {
      alive = false;
    };
  }, []);
  const disabled =
    busy ||
    game.busy ||
    !!game.state?.downed ||
    account.account?.character?.downed ||
    !!game.state?.combat;
  async function trade(itemId: number, upgradeCode?: Upgrade["code"]) {
    /* 중복 클릭을 차단하고 거래 결과와 잔액을 동기화한다. */
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setNotice("");
    try {
      await api(
        upgradeCode ? "/shop/upgrades/buy" : `/shop/${mode}`,
        upgradeCode
          ? { code: upgradeCode, quantity }
          : { item_id: itemId, quantity },
      );
      await game.reload();
      await account.reloadAccount();
      setNotice(mode === "buy" ? "구매 완료" : "판매 완료");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "거래 실패");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }
  const rows =
    mode === "buy"
      ? products.map((row) => ({
          ...row,
          price: row.buy_price,
          owned: undefined as number | undefined,
        }))
      : (game.inventory?.items ?? []).map((row) => ({
          ...row,
          price: row.sell_price,
          owned: row.quantity,
        }));
  return (
    <div className={styles.shopWorkspace}>
      <section className={styles.shopNpc}>
        <div>
          <div className={sharedStyles.smallLabel} data-ui="smallLabel">
            SUPPLY / QUARTERMASTER
          </div>
          <h1>보급 상점</h1>
          <p>필요한 물자를 고르세요.</p>
          <strong>
            {(
              game.inventory?.money ??
              account.account?.money ??
              0
            ).toLocaleString()}{" "}
            C
          </strong>
        </div>
        <img src="/npc/quartermaster.png" alt="보급 상점의 NPC" />
      </section>
      <section className={sharedStyles.panel} data-ui="panel">
        <div className={styles.shopToolbar}>
          <div>
            <button
              aria-pressed={mode === "buy"}
              onClick={() => {
                /* 구매 목록을 연다. */ setMode("buy");
                setQuantity(1);
              }}
            >
              구매
            </button>
            <button
              aria-pressed={mode === "sell"}
              onClick={() => {
                /* 실제 보유 물품만 판매 목록에 표시한다. */ setMode("sell");
                setQuantity(1);
              }}
            >
              판매
            </button>
          </div>
          <label>
            수량{" "}
            <input
              type="number"
              min={1}
              max={99}
              value={quantity}
              onChange={(event) => {
                /* 거래 수량을 제한한다. */ setQuantity(
                  Math.max(1, Math.min(99, Number(event.target.value) || 1)),
                );
              }}
            />
          </label>
        </div>
        {notice && <p role="status">{notice}</p>}
        {disabled && (
          <p className={sharedStyles.helpText} data-ui="helpText">
            전투·빈사 상태에서는 거래할 수 없어.
          </p>
        )}
        <div className={styles.shopProducts}>
          {mode === "buy" &&
            upgrades.map((product) => (
              <article key={product.code} className={styles.upgradeProduct}>
                <div>
                  <h3>{product.name}</h3>
                  <p>{product.description}</p>
                </div>
                <div>
                  <strong>{product.price.toLocaleString()} C</strong>
                  <button
                    disabled={disabled}
                    onClick={() => void trade(0, product.code)}
                    aria-label={`${product.name} 구매`}
                  >
                    구매
                  </button>
                </div>
              </article>
            ))}
          {rows.map((row) => {
            /* 상품별 서버 가격과 소지 수량을 표시한다. */ return (
              <article
                key={row.item_id}
                className={classNames(
                  itemFrame(row.rarity),
                  styles.itemProduct,
                )}
              >
                <ItemIndicators rarity={row.rarity} edible={row.edible} />
                <div>
                  <h3>{row.name}</h3>
                  <p>{row.description}</p>
                  <small>
                    {kilograms(row.weight_grams)} kg{" "}
                    {row.owned !== undefined && `· 보유 ${row.owned}개`}
                  </small>
                </div>
                <div>
                  <strong>{row.price.toLocaleString()} C</strong>
                  <button
                    disabled={
                      disabled ||
                      !row.price ||
                      (row.owned !== undefined && quantity > row.owned)
                    }
                    onClick={() => {
                      /* 선택한 상품을 지정 수량으로 거래한다. */ void trade(
                        row.item_id,
                      );
                    }}
                  >
                    {mode === "buy" ? "구매" : "판매"}
                  </button>
                </div>
              </article>
            );
          })}
        </div>
        {mode === "sell" && !rows.length && <p>판매할 물품이 없어.</p>}
      </section>
    </div>
  );
}
