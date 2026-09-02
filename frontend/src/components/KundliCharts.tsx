"use client";

/** North Indian (house-fixed diamond) and South Indian (sign-fixed grid)
 *  kundli renderers. Pure SVG, no chart libraries. */

import type { ChartV1 } from "@/lib/types";
import { GRAHA_ABBR } from "@/lib/types";

const GOLD = "#c9a227";
const LINE = "#8a7a4d";
const TEXT = "#ede6d6";
const DIM = "#9c8f6f";

function planetsBySign(chart: ChartV1): Record<number, string[]> {
  const out: Record<number, string[]> = {};
  for (const [key, g] of Object.entries(chart.grahas)) {
    const label = GRAHA_ABBR[key] + (g.retrograde && key !== "rahu" && key !== "ketu" ? "℞" : "");
    (out[g.sign] ||= []).push(label);
  }
  return out;
}

// ── South Indian: fixed sign positions on a 4×4 grid ─────────────────────────
const SOUTH_POS: Record<number, [number, number]> = {
  11: [0, 0], 0: [0, 1], 1: [0, 2], 2: [0, 3],
  10: [1, 0], 3: [1, 3],
  9: [2, 0], 4: [2, 3],
  8: [3, 0], 7: [3, 1], 6: [3, 2], 5: [3, 3],
};

export function SouthChart({ chart, size = 380 }: { chart: ChartV1; size?: number }) {
  const cell = size / 4;
  const bySign = planetsBySign(chart);
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[420px]">
      <rect x="0" y="0" width={size} height={size} fill="none" stroke={GOLD} strokeWidth="2" />
      {Object.entries(SOUTH_POS).map(([signStr, [row, col]]) => {
        const sign = Number(signStr);
        const x = col * cell, y = row * cell;
        const isLagna = sign === chart.lagna.sign;
        const planets = bySign[sign] || [];
        return (
          <g key={sign}>
            <rect x={x} y={y} width={cell} height={cell} fill={isLagna ? "rgba(201,162,39,0.12)" : "none"}
                  stroke={LINE} strokeWidth="1" />
            {isLagna && (
              <line x1={x} y1={y + 14} x2={x + 14} y2={y} stroke={GOLD} strokeWidth="2" />
            )}
            {planets.map((p, i) => (
              <text key={p} x={x + cell / 2} y={y + 22 + i * 15} textAnchor="middle"
                    fontSize="13" fill={TEXT} fontWeight="600">{p}</text>
            ))}
          </g>
        );
      })}
      <text x={size / 2} y={size / 2 - 6} textAnchor="middle" fontSize="13" fill={DIM}>
        {chart.input.date}
      </text>
      <text x={size / 2} y={size / 2 + 12} textAnchor="middle" fontSize="12" fill={DIM}>
        Lagna: {chart.lagna.sign_name}
      </text>
    </svg>
  );
}

// ── North Indian: fixed house positions in the diamond ───────────────────────
type Pt = [number, number];

function northRegions(S: number): { house: number; poly: Pt[]; label: Pt }[] {
  const C: Pt = [S / 2, S / 2];
  const MT: Pt = [S / 2, 0], MR: Pt = [S, S / 2], MB: Pt = [S / 2, S], ML: Pt = [0, S / 2];
  const q1: Pt = [S / 4, S / 4], q2: Pt = [(3 * S) / 4, S / 4];
  const q3: Pt = [S / 4, (3 * S) / 4], q4: Pt = [(3 * S) / 4, (3 * S) / 4];
  const TL: Pt = [0, 0], TR: Pt = [S, 0], BL: Pt = [0, S], BR: Pt = [S, S];
  const centroid = (pts: Pt[]): Pt => [
    pts.reduce((a, p) => a + p[0], 0) / pts.length,
    pts.reduce((a, p) => a + p[1], 0) / pts.length,
  ];
  const defs: [number, Pt[]][] = [
    [1, [MT, q1, C, q2]],
    [2, [TL, MT, q1]],
    [3, [TL, q1, ML]],
    [4, [ML, q1, C, q3]],
    [5, [BL, ML, q3]],
    [6, [BL, q3, MB]],
    [7, [MB, q3, C, q4]],
    [8, [BR, MB, q4]],
    [9, [BR, q4, MR]],
    [10, [MR, q4, C, q2]],
    [11, [TR, MR, q2]],
    [12, [TR, q2, MT]],
  ];
  return defs.map(([house, poly]) => ({ house, poly, label: centroid(poly) }));
}

export function NorthChart({ chart, size = 380 }: { chart: ChartV1; size?: number }) {
  const regions = northRegions(size);
  const lagnaSign = chart.lagna.sign;
  const byHouse: Record<number, string[]> = {};
  for (const [key, g] of Object.entries(chart.grahas)) {
    const label = GRAHA_ABBR[key] + (g.retrograde && key !== "rahu" && key !== "ketu" ? "℞" : "");
    (byHouse[g.house] ||= []).push(label);
  }
  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="w-full max-w-[420px]">
      <rect x="0" y="0" width={size} height={size} fill="none" stroke={GOLD} strokeWidth="2" />
      <line x1="0" y1="0" x2={size} y2={size} stroke={LINE} />
      <line x1={size} y1="0" x2="0" y2={size} stroke={LINE} />
      <polygon points={`${size / 2},0 ${size},${size / 2} ${size / 2},${size} 0,${size / 2}`}
               fill="none" stroke={LINE} />
      {regions.map(({ house, poly, label }) => {
        const sign = (lagnaSign + house - 1) % 12;
        const planets = byHouse[house] || [];
        const isLagnaHouse = house === 1;
        return (
          <g key={house}>
            {isLagnaHouse && (
              <polygon points={poly.map((p) => p.join(",")).join(" ")}
                       fill="rgba(201,162,39,0.10)" stroke="none" />
            )}
            <text x={label[0]} y={label[1] - (planets.length ? 10 : 0)} textAnchor="middle"
                  fontSize="11" fill={DIM}>{sign + 1}</text>
            {planets.map((p, i) => (
              <text key={p} x={label[0]} y={label[1] + 6 + i * 13} textAnchor="middle"
                    fontSize="12" fill={TEXT} fontWeight="600">{p}</text>
            ))}
          </g>
        );
      })}
    </svg>
  );
}
