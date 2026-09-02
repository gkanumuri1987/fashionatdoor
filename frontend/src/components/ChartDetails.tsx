"use client";

import type { ChartV1 } from "@/lib/types";
import { GRAHA_LABEL } from "@/lib/types";

const DIGNITY_COLOR: Record<string, string> = {
  exalted: "text-emerald-400",
  moolatrikona: "text-emerald-300",
  own: "text-amber-300",
  great_friend: "text-lime-300",
  friend: "text-lime-200",
  neutral: "text-stone-300",
  enemy: "text-orange-300",
  great_enemy: "text-red-400",
  debilitated: "text-red-400",
};

export function PlanetTable({ chart }: { chart: ChartV1 }) {
  return (
    <div className="overflow-x-auto rounded-lg border border-[#3d2f5c]">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-[#241640] text-left text-[#c9a227]">
            <th className="px-3 py-2">Graha</th>
            <th className="px-3 py-2">Sign</th>
            <th className="px-3 py-2">Degree</th>
            <th className="px-3 py-2">House</th>
            <th className="px-3 py-2">Nakshatra</th>
            <th className="px-3 py-2">Dignity</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(chart.grahas).map(([key, g]) => (
            <tr key={key} className="border-t border-[#3d2f5c]/60">
              <td className="px-3 py-2 font-medium">
                {GRAHA_LABEL[key]}
                {g.retrograde && key !== "rahu" && key !== "ketu" && (
                  <span className="ml-1 text-xs text-orange-300">℞</span>
                )}
                {g.combust && <span className="ml-1 text-xs text-red-300">☉c</span>}
              </td>
              <td className="px-3 py-2">{g.sign_name}</td>
              <td className="px-3 py-2 tabular-nums">{g.degree_in_sign}</td>
              <td className="px-3 py-2">{g.house}</td>
              <td className="px-3 py-2">
                {g.nakshatra.name} <span className="text-[#9c8f6f]">p{g.nakshatra.pada}</span>
              </td>
              <td className={`px-3 py-2 ${DIGNITY_COLOR[g.dignity] || ""}`}>
                {g.dignity.replace("_", " ")}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DashaTimeline({ chart }: { chart: ChartV1 }) {
  const cur = chart.current_dasha;
  return (
    <div className="space-y-3">
      {cur && (
        <div className="rounded-lg border border-[#c9a227]/50 bg-[#c9a227]/10 p-3 text-sm">
          <span className="font-semibold text-[#c9a227]">Now running: </span>
          {cur.maha} mahadasha → {cur.antar} antardasha → {cur.pratyantar} pratyantar
          <span className="text-[#9c8f6f]"> (antar ends {cur.antar_end.slice(0, 10)})</span>
        </div>
      )}
      <div className="text-xs text-[#9c8f6f]">
        Balance at birth: {chart.vimshottari.balance_at_birth_years.toFixed(2)} years of{" "}
        {chart.vimshottari.mahadashas[0].lord} · Moon in {chart.vimshottari.moon_nakshatra}
      </div>
      <div className="space-y-1">
        {chart.vimshottari.mahadashas.map((m) => {
          const active = cur?.maha === m.lord;
          return (
            <details key={m.lord + m.start} className="group rounded-lg border border-[#3d2f5c]/60">
              <summary
                className={`flex cursor-pointer items-center justify-between px-3 py-2 text-sm ${
                  active ? "bg-[#c9a227]/10 text-[#c9a227]" : ""
                }`}
              >
                <span className="font-medium capitalize">{m.lord} · {m.years}y</span>
                <span className="tabular-nums text-[#9c8f6f]">
                  {m.start.slice(0, 10)} → {m.end.slice(0, 10)}
                </span>
              </summary>
              <div className="border-t border-[#3d2f5c]/40 px-3 py-2">
                {m.antardashas?.map((a) => (
                  <div key={a.lord + a.start}
                       className="flex justify-between py-0.5 text-xs text-[#cbbfa4]">
                    <span className="capitalize">{m.lord}–{a.lord}</span>
                    <span className="tabular-nums">{a.start.slice(0, 10)} → {a.end.slice(0, 10)}</span>
                  </div>
                ))}
              </div>
            </details>
          );
        })}
      </div>
    </div>
  );
}

export function PanchangaYogas({ chart }: { chart: ChartV1 }) {
  const p = chart.panchanga;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-2 text-sm sm:grid-cols-3">
        {[
          ["Tithi", `${p.tithi.name}`],
          ["Vara", p.vara.name],
          ["Nakshatra", `${p.nakshatra.name} p${p.nakshatra.pada}`],
          ["Yoga", p.yoga.name],
          ["Karana", p.karana.name],
          ["Moon sign", chart.moon_sign_name],
        ].map(([k, v]) => (
          <div key={k} className="rounded-lg border border-[#3d2f5c]/60 p-3">
            <div className="text-xs text-[#9c8f6f]">{k}</div>
            <div className="font-medium">{v}</div>
          </div>
        ))}
      </div>
      <div>
        <h3 className="mb-2 text-sm font-semibold text-[#c9a227]">Yogas present</h3>
        {chart.yogas.length === 0 && (
          <div className="text-sm text-[#9c8f6f]">No major classical yogas detected.</div>
        )}
        <div className="space-y-1">
          {chart.yogas.map((y) => (
            <div key={y.key} className="rounded-lg border border-[#3d2f5c]/60 p-2 text-sm">
              <span className="font-medium">{y.name}</span>
              <span className="ml-2 text-xs text-[#9c8f6f]">{y.factors.join("; ")}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
