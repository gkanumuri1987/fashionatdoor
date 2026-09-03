"use client";

/** Vastu floor-plan analysis: upload → vision extracts rooms/zones →
 *  deterministic classical rules judge → AI narrates the computed findings.
 *  The plan image is analyzed in memory server-side and never stored. */

import Link from "next/link";
import { useState } from "react";
import { LangSwitcher, useLang } from "@/lib/i18n";
import { compressImage } from "@/lib/image";

const DIRECTIONS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];

interface Finding {
  label: string; type: string; zone: string; verdict: string;
  classical_position?: string[]; soft_remedy?: string; note?: string;
}
interface VastuResult {
  usable?: boolean; reason?: string;
  findings?: Finding[]; score?: number; score_out_of?: number;
  brahmasthan?: { blocked_by: string | null; note: string };
  narrative?: string | null; disclaimer?: string;
}

const VERDICT_COLOR: Record<string, string> = {
  excellent: "text-emerald-400", good: "text-emerald-300", neutral: "text-[#cbbfa4]",
  avoid: "text-orange-400", grave: "text-red-400", unknown: "text-[#6f6350]",
};

export default function VastuPage() {
  const { lang, t } = useLang();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [topDir, setTopDir] = useState("N");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<VastuResult | null>(null);

  async function analyze() {
    if (!file) return;
    setBusy(true); setError(""); setResult(null);
    try {
      const form = new FormData();
      form.append("plan", file);
      form.append("top_direction", topDir);
      form.append("language", lang);
      const res = await fetch("/api/vastu", { method: "POST", body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("generic_error"));
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <div className="mb-2 flex justify-end"><LangSwitcher /></div>
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-[#c9a227]">{t("vastu_title")}</h1>
        <p className="mt-1 text-sm text-[#9c8f6f]">{t("vastu_sub")}</p>
        <Link href="/" className="mt-2 inline-block text-xs text-[#c9a227] underline">
          {t("back_to_chart")}
        </Link>
      </header>

      <section className="space-y-4 rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5">
        <div className="rounded-xl border border-dashed border-[#3d2f5c] p-5 text-center">
          <input id="plan-input" type="file" accept="image/*" className="hidden"
                 onChange={async (e) => {
                   const raw = e.target.files?.[0] ?? null;
                   const f = raw ? await compressImage(raw) : null;
                   setFile(f);
                   setPreview(f ? URL.createObjectURL(f) : "");
                 }} />
          <label htmlFor="plan-input"
                 className="inline-block cursor-pointer rounded-lg bg-[#c9a227] px-5 py-2 font-semibold text-[#140b26]">
            {t("vastu_pick")}
          </label>
          {preview && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={preview} alt="floor plan preview"
                 className="mx-auto mt-4 max-h-64 rounded-lg border border-[#3d2f5c]" />
          )}
        </div>

        <label className="block text-sm">
          <span className="text-[#9c8f6f]">{t("vastu_top_dir")}</span>
          <select value={topDir} onChange={(e) => setTopDir(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2">
            {DIRECTIONS.map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </label>

        <button onClick={analyze} disabled={!file || busy}
                className="w-full rounded-lg bg-[#c9a227] px-5 py-3 font-semibold text-[#140b26] disabled:opacity-40">
          {busy ? t("vastu_busy") : t("vastu_analyze")}
        </button>
        {error && <p className="text-sm text-red-400">{error}</p>}
        {result && result.usable === false && (
          <p className="rounded-lg border border-orange-500/40 bg-orange-500/10 p-3 text-sm text-orange-200">
            {result.reason}
          </p>
        )}
      </section>

      {result?.usable && (
        <section className="mt-6 space-y-4">
          <div className="rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-center">
            <div className="text-3xl font-bold text-[#c9a227]">
              {result.score} <span className="text-lg text-[#9c8f6f]">/ {result.score_out_of}</span>
            </div>
            <div className="mt-1 text-xs text-[#9c8f6f]">{t("vastu_score")}</div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-[#3d2f5c]">
            <table className="w-full text-sm">
              <thead><tr className="bg-[#241640] text-left text-[#c9a227]">
                <th className="px-3 py-2">{t("vastu_room")}</th>
                <th className="px-3 py-2">{t("vastu_zone")}</th>
                <th className="px-3 py-2">{t("vastu_verdict")}</th>
              </tr></thead>
              <tbody>
                {result.findings?.map((f, i) => (
                  <tr key={i} className="border-t border-[#3d2f5c]/60 align-top">
                    <td className="px-3 py-2">{f.label} <span className="text-xs text-[#6f6350]">({f.type})</span></td>
                    <td className="px-3 py-2">{f.zone}</td>
                    <td className={`px-3 py-2 ${VERDICT_COLOR[f.verdict] ?? ""}`}>
                      {f.verdict}
                      {f.soft_remedy && (
                        <div className="mt-1 text-xs text-[#9c8f6f]">{f.soft_remedy}</div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {result.brahmasthan && (
            <p className={`rounded-lg border p-3 text-sm ${result.brahmasthan.blocked_by
              ? "border-red-500/40 bg-red-500/10 text-red-200"
              : "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"}`}>
              {result.brahmasthan.note}
            </p>
          )}
          {result.narrative && (
            <div className="whitespace-pre-wrap rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-sm leading-relaxed">
              {result.narrative}
            </div>
          )}
          <p className="text-center text-xs text-[#9c8f6f]">{t("vastu_not_stored")}</p>
          <p className="text-xs text-[#9c8f6f]">{result.disclaimer}</p>
        </section>
      )}

      <footer className="mt-10 text-center text-xs text-[#9c8f6f]">{t("disclaimer")}</footer>
    </main>
  );
}
