"use client";

import Link from "next/link";
import { useState } from "react";
import { BirthForm, type BirthValue } from "@/components/BirthForm";

interface Koota {
  koota: string; max: number; points: number; boy: string; girl: string;
  dosha?: boolean; exception?: string | null;
}
interface Milan {
  total: number; max: number; verdict: string; kootas: Koota[];
  manglik_note: string; doshas: string[]; disclaimer: string;
  boy: { moon_sign: string; nakshatra: string };
  girl: { moon_sign: string; nakshatra: string };
}

const VERDICT_LABEL: Record<string, [string, string]> = {
  excellent: ["Excellent match", "text-emerald-400"],
  very_good: ["Very good match", "text-emerald-300"],
  acceptable: ["Acceptable match", "text-amber-300"],
  below_threshold: ["Below traditional threshold", "text-orange-400"],
};

const empty = (): BirthValue => ({ date: "", time: "", lat: null, lng: null, placeName: "" });

export default function MatchPage() {
  const [boy, setBoy] = useState<BirthValue>(empty());
  const [girl, setGirl] = useState<BirthValue>(empty());
  const [milan, setMilan] = useState<Milan | null>(null);
  const [narrative, setNarrative] = useState("");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [narrLoading, setNarrLoading] = useState(false);
  const [error, setError] = useState("");

  const ready = (v: BirthValue) => v.date && v.time && v.lat !== null;

  async function runMatch() {
    if (!ready(boy) || !ready(girl)) {
      setError("Fill both birth details and pick places from the suggestions.");
      return;
    }
    setLoading(true); setError(""); setNarrative("");
    try {
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          boy: { date: boy.date, time: boy.time, lat: boy.lat, lng: boy.lng },
          girl: { date: girl.date, time: girl.time, lat: girl.lat, lng: girl.lng },
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Match failed");
      setMilan(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function fetchNarrative() {
    if (!milan) return;
    setNarrLoading(true); setError("");
    try {
      const res = await fetch("/api/match/narrative", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ milan, language }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Narrative failed");
      setNarrative(data.text);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setNarrLoading(false);
    }
  }

  const verdict = milan ? VERDICT_LABEL[milan.verdict] ?? [milan.verdict, ""] : null;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-[#c9a227]">Kundli Milan</h1>
        <p className="mt-1 text-sm text-[#9c8f6f]">Ashtakoota 36-guna matching + Manglik analysis — computed, never guessed</p>
        <Link href="/" className="mt-2 inline-block text-xs text-[#c9a227] underline">← Birth chart</Link>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <BirthForm label="Boy / Groom" value={boy} onChange={setBoy} />
        <BirthForm label="Girl / Bride" value={girl} onChange={setGirl} />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button onClick={runMatch} disabled={loading}
                className="rounded-lg bg-[#c9a227] px-5 py-2 font-semibold text-[#140b26] hover:bg-[#dcb63a] disabled:opacity-50">
          {loading ? "Matching…" : "Match Kundlis"}
        </button>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>

      {milan && verdict && (
        <section className="mt-8 space-y-4">
          <div className="rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-center">
            <div className="text-4xl font-bold text-[#c9a227]">{milan.total} <span className="text-lg text-[#9c8f6f]">/ {milan.max}</span></div>
            <div className={`mt-1 font-semibold ${verdict[1]}`}>{verdict[0]}</div>
            <div className="mt-2 text-xs text-[#9c8f6f]">
              {milan.boy.moon_sign} moon · {milan.boy.nakshatra} ↔ {milan.girl.moon_sign} moon · {milan.girl.nakshatra}
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-[#3d2f5c]">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#241640] text-left text-[#c9a227]">
                  <th className="px-3 py-2">Koota</th><th className="px-3 py-2">Boy</th>
                  <th className="px-3 py-2">Girl</th><th className="px-3 py-2 text-right">Points</th>
                </tr>
              </thead>
              <tbody>
                {milan.kootas.map((k) => (
                  <tr key={k.koota} className="border-t border-[#3d2f5c]/60">
                    <td className="px-3 py-2 font-medium capitalize">
                      {k.koota.replace("_", " ")}
                      {k.dosha && <span className="ml-2 rounded bg-orange-500/20 px-1.5 py-0.5 text-xs text-orange-300">dosha</span>}
                    </td>
                    <td className="px-3 py-2 capitalize">{k.boy}</td>
                    <td className="px-3 py-2 capitalize">{k.girl}</td>
                    <td className={`px-3 py-2 text-right tabular-nums ${k.points === 0 ? "text-orange-400" : ""}`}>
                      {k.points} / {k.max}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {milan.kootas.filter((k) => k.exception).map((k) => (
            <div key={k.koota} className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-xs text-amber-200">
              <b className="capitalize">{k.koota} exception:</b> {k.exception}
            </div>
          ))}

          <div className="rounded-lg border border-[#3d2f5c] p-3 text-sm">{milan.manglik_note}</div>

          <div className="flex items-center gap-3">
            <select value={language} onChange={(e) => setLanguage(e.target.value)}
                    className="rounded-lg border border-[#3d2f5c] bg-[#140b26] px-2 py-2 text-sm">
              <option value="en">English</option>
              <option value="te">తెలుగు</option>
              <option value="hi">हिन्दी</option>
            </select>
            <button onClick={fetchNarrative} disabled={narrLoading}
                    className="rounded-lg border border-[#c9a227] px-4 py-2 text-sm font-semibold text-[#c9a227] hover:bg-[#c9a227]/10 disabled:opacity-50">
              {narrLoading ? "Writing…" : "AI compatibility reading"}
            </button>
          </div>
          {narrative && (
            <div className="whitespace-pre-wrap rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-sm leading-relaxed">
              {narrative}
            </div>
          )}
          <p className="text-xs text-[#9c8f6f]">{milan.disclaimer}</p>
        </section>
      )}
    </main>
  );
}
