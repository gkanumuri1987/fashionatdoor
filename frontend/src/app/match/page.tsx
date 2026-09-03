"use client";

import Link from "next/link";
import { useState } from "react";
import { BirthForm, type BirthValue } from "@/components/BirthForm";
import { LangSwitcher, useLang } from "@/lib/i18n";

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
  excellent: ["verdict_excellent", "text-emerald-400"],
  very_good: ["verdict_very_good", "text-emerald-300"],
  acceptable: ["verdict_acceptable", "text-amber-300"],
  below_threshold: ["verdict_below", "text-orange-400"],
};

const empty = (): BirthValue => ({ date: "", time: "", lat: null, lng: null, placeName: "" });

export default function MatchPage() {
  const { lang, t } = useLang();
  const [boy, setBoy] = useState<BirthValue>(empty());
  const [girl, setGirl] = useState<BirthValue>(empty());
  const [milan, setMilan] = useState<Milan | null>(null);
  const [narrative, setNarrative] = useState("");
  const [loading, setLoading] = useState(false);
  const [narrLoading, setNarrLoading] = useState(false);
  const [error, setError] = useState("");

  const ready = (v: BirthValue) => v.date && v.time && v.lat !== null;

  async function runMatch() {
    if (!ready(boy) || !ready(girl)) {
      setError(t("fill_both"));
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
      setError(e instanceof Error ? e.message : t("generic_error"));
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
        body: JSON.stringify({ milan, language: lang }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Narrative failed");
      setNarrative(data.text);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setNarrLoading(false);
    }
  }

  const verdict = milan ? VERDICT_LABEL[milan.verdict] ?? [milan.verdict, ""] : null;

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8 text-center">
        <div className="mb-2 flex justify-end"><LangSwitcher /></div>
        <h1 className="heading-display text-4xl">{t("milan_title")}</h1>
        <div className="ornament mt-2 text-xs">✦</div>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">{t("milan_tagline")}</p>
        <Link href="/" className="mt-2 inline-block text-xs text-[var(--gold)] underline">{t("back_to_chart")}</Link>
      </header>

      <div className="grid gap-4 sm:grid-cols-2">
        <BirthForm label={t("boy_groom")} value={boy} onChange={setBoy} />
        <BirthForm label={t("girl_bride")} value={girl} onChange={setGirl} />
      </div>

      <div className="mt-4 flex items-center gap-3">
        <button onClick={runMatch} disabled={loading}
                className="btn-gold">
          {loading ? t("matching") : t("match_btn")}
        </button>
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>

      {milan && verdict && (
        <section className="mt-8 space-y-4">
          <div className="card p-5 text-center">
            <div className="text-4xl font-bold text-[var(--gold)]">{milan.total} <span className="text-lg text-[var(--ink-muted)]">/ {milan.max}</span></div>
            <div className={`mt-1 font-semibold ${verdict[1]}`}>{t(verdict[0])}</div>
            <div className="mt-2 text-xs text-[var(--ink-muted)]">
              {milan.boy.moon_sign} moon · {milan.boy.nakshatra} ↔ {milan.girl.moon_sign} moon · {milan.girl.nakshatra}
            </div>
          </div>

          <div className="overflow-x-auto rounded-lg border border-[var(--line)]">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[var(--surface-raised)] text-left text-[var(--gold)]">
                  <th className="px-3 py-2">{t("koota")}</th><th className="px-3 py-2">{t("boy_col")}</th>
                  <th className="px-3 py-2">{t("girl_col")}</th><th className="px-3 py-2 text-right">{t("points")}</th>
                </tr>
              </thead>
              <tbody>
                {milan.kootas.map((k) => (
                  <tr key={k.koota} className="border-t border-[var(--line-soft)]">
                    <td className="px-3 py-2 font-medium capitalize">
                      {k.koota.replace("_", " ")}
                      {k.dosha && <span className="ml-2 rounded bg-orange-500/20 px-1.5 py-0.5 text-xs text-orange-300">{t("dosha")}</span>}
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
              <b className="capitalize">{k.koota} — {t("exception")}:</b> {k.exception}
            </div>
          ))}

          <div className="rounded-lg border border-[var(--line)] p-3 text-sm">{milan.manglik_note}</div>

          <div className="flex items-center gap-3">
            <button onClick={fetchNarrative} disabled={narrLoading}
                    className="btn-ghost text-sm font-semibold">
              {narrLoading ? t("writing") : t("ai_compat")}
            </button>
          </div>
          {narrative && (
            <div className="card whitespace-pre-wrap p-5 text-sm leading-relaxed">
              {narrative}
            </div>
          )}
          <p className="text-xs text-[var(--ink-muted)]">{milan.disclaimer}</p>
        </section>
      )}
    </main>
  );
}
