/* 전체 구역 선택 지도와 현재 탐색 구역의 평면 관측 지도를 그린다. */
"use client";

import styles from "./Observation.module.css";
import { classNames } from "../../lib/classNames";
import type { WorldMap } from "../../lib/exploration";
import { MAP_ZONES, PATROL_ROUTE, zoneFor } from "../../lib/droneMap";
type Props = {
  maps: WorldMap[];
  selected?: WorldMap;
  active: boolean;
  step: number;
  blocked: boolean;
  onSelect: (id: number) => void;
};
const overviewBlocks = Array.from(
  {
    length: 160,
  },
  (_, index) => {
    /* 규칙적인 도시 블록을 고정 값으로 생성하여 재렌더링 시 지형을 보존한다. */
    const col = index % 16,
      row = Math.floor(index / 16);
    return {
      x: 28 + col * 74 + (row % 2) * 12,
      y: 36 + row * 68,
      width: 26 + ((index * 7) % 24),
      height: 20 + ((index * 11) % 28),
    };
  },
);
export function DroneMap({
  maps,
  selected,
  active,
  step,
  blocked,
  onSelect,
}: Props) {
  /* 실제 서버에 저장된 탐색 횟수로 레이더 위치를 복원한다. */
  const point = PATROL_ROUTE[step % PATROL_ROUTE.length];
  const progress = PATROL_ROUTE.slice(
    Math.max(0, (step % PATROL_ROUTE.length) - 5),
    (step % PATROL_ROUTE.length) + 1,
  );
  const zoneIndex = Math.max(
    0,
    MAP_ZONES.findIndex((zone) => zone.name === selected?.name),
  );
  return (
    <div className={styles.droneMapLayer}>
      <svg
        className={styles.droneMapSvg}
        viewBox="0 0 1200 720"
        preserveAspectRatio="none"
        role="img"
        aria-label={
          active ? `${selected?.name} 탐사 위치 지도` : "균열 구역 전체 지도"
        }
      >
        <defs>
          <pattern
            id="drone-grid"
            width="60"
            height="60"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M60 0H0V60"
              fill="none"
              stroke="#789186"
              strokeOpacity=".08"
            />
          </pattern>
        </defs>
        <rect width="1200" height="720" fill="var(--map-ground)" />
        {active ? (
          <g>
            <path
              d="M0 80H1200M0 640H1200M110 0V720M740 0V720M1090 0V720"
              stroke="var(--map-road)"
              strokeWidth="38"
            />
            <path
              d="M0 80H1200M0 640H1200M110 0V720M740 0V720M1090 0V720"
              stroke="var(--map-road-line)"
              strokeWidth="2"
            />
            {Array.from(
              {
                length: 7,
              },
              (_, index) => {
                /* 구역에 따라 창고·주거·병동 블록의 너비와 간격을 달리한다. */
                const y = 125 + index * 68;
                return (
                  <g key={index}>
                    <rect
                      x="225"
                      y={y}
                      width={zoneIndex === 3 ? 370 : 80 + (index % 3) * 65}
                      height="44"
                      fill="var(--map-block)"
                      stroke="#597069"
                    />
                    <rect
                      x="815"
                      y={y}
                      width={110 + (index % 2) * 85}
                      height="44"
                      fill="var(--map-block)"
                    />
                  </g>
                );
              },
            )}
            <path
              d="M180 530H650V240H180V530"
              stroke="#425b50"
              strokeWidth="18"
              fill="none"
            />
            <polyline
              points={progress
                .map(([x, y]) => {
                  /* 최근 이동 구간을 점선으로 연결한다. */ return `${x},${y}`;
                })
                .join(" ")}
              stroke="#7cdbac"
              strokeWidth="3"
              strokeDasharray="3 9"
              fill="none"
            />
            <g transform={`translate(${point[0]},${point[1]})`}>
              <circle className={styles.radarWave} r="28" />
              <circle
                className={classNames(styles.radarWave, styles.radarWaveSecond)}
                r="48"
              />
              <circle r="7" fill="#91f5be" />
              <path d="M0 -16V-24M0 16V24M-16 0H-24M16 0H24" stroke="#a7f6cb" />
            </g>
          </g>
        ) : (
          <g>
            {overviewBlocks.map((block, index) => {
              /* 평면 건물 구획을 표시한다. */ return (
                <rect
                  key={index}
                  {...block}
                  fill={index % 4 === 0 ? "var(--map-block)" : "#2e4a48"}
                />
              );
            })}
            <path
              d="M390 -40C610 100 360 210 500 345S790 500 720 760"
              fill="none"
              stroke="var(--map-road)"
              strokeWidth="105"
            />
            <path
              d="M-20 275L350 230L680 200L1220 70M-20 440L290 410L690 450L1220 540M200 -20L300 720M830 -20L920 720"
              stroke="var(--map-road)"
              strokeWidth="20"
              fill="none"
            />
            <path
              d="M-20 275L350 230L680 200L1220 70M-20 440L290 410L690 450L1220 540M200 -20L300 720M830 -20L920 720"
              stroke="var(--map-road-line)"
              strokeWidth="2"
              fill="none"
            />
            {selected &&
              (() => {
                /* 선택 구역만 황록색으로 강조한다. */ const zone = zoneFor(
                  selected.name,
                );
                return (
                  <rect
                    x={zone.x - 46}
                    y={zone.y - 36}
                    width="132"
                    height="88"
                    fill="var(--selection-color)"
                    fillOpacity=".35"
                    stroke="var(--selection-color)"
                    strokeDasharray="8 5"
                  />
                );
              })()}
          </g>
        )}
        <rect width="1200" height="720" fill="url(#drone-grid)" />
      </svg>
      {active && (
        <div className={styles.droneMapLabels} aria-hidden="true">
          <span
            className={styles.mapTextLabel}
            style={{ left: "20%", top: "29.6%" }}
          >
            {selected?.name}
          </span>
          <span
            className={styles.mapTextLabel}
            style={{ left: "68.3%", top: "84.7%" }}
          >
            진입 도로
          </span>
          <span
            className={styles.radarTextLabel}
            style={{ left: `${point[0] / 12}%`, top: `${point[1] / 7.2}%` }}
          >
            피계약자
          </span>
        </div>
      )}
      {!active && (
        <div className={styles.droneMapMarkers}>
          {maps.map((map, index) => {
            /* 접근 가능한 실제 맵을 키보드로도 선택 가능한 버튼으로 표시한다. */
            const zone = zoneFor(map.name, index);
            return (
              <button
                key={map.id}
                type="button"
                className={classNames(
                  styles.droneMapMarker,
                  selected?.id === map.id ? styles.isSelected : "",
                )}
                style={{
                  left: `${zone.x / 12}%`,
                  top: `${zone.y / 7.2}%`,
                }}
                disabled={blocked}
                aria-label={map.name}
                title={map.name}
                aria-pressed={selected?.id === map.id}
                onClick={() => {
                  /* 구역을 선택하고 진입 전 상태는 유지한다. */ onSelect(
                    map.id,
                  );
                }}
                data-ui={selected?.id === map.id ? "" : ""}
              >
                <b>{String(index + 1).padStart(2, "0")}</b>
                <span>{map.name}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
