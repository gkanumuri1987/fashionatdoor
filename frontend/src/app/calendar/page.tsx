"use client";

/** Panchanga & Festival Calendar — tradition + timezone aware, printable.
 *  Every cell: tithi (with local end time), nakshatra, festivals; Tamil mode
 *  shows solar month/day. "Download PDF" uses the print stylesheet; "Add to
 *  calendar (.ics)" exports the month's festivals. */

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";

const MONTHS = ["January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"];
const LOCATIONS = [
  { key: "in", label: "🇮🇳 India" }, { key: "uk", label: "🇬🇧 UK" },
  { key: "us_east", label: "🇺🇸 US East" }, { key: "us_west", label: "🇺🇸 US West" },
  { key: "au", label: "🇦🇺 Australia" },
];
const TRADITIONS = [
  { key: "telugu", label: "తెలుగు · Telugu" }, { key: "tamil", label: "தமிழ் · Tamil" },
  { key: "kannada", label: "ಕನ್ನಡ · Kannada" }, { key: "hindi", label: "हिन्दी · North Indian" },
];
const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

interface CalDay {
  date: string; day: number; weekday: number; vara: string;
  sunrise: string | null; sunset: string | null;
  tithi: { name: string; paksha: string; number: number; ends: string | null };
  nakshatra: { name: string; ends: string | null };
  masa: string; masa_adhika: boolean; tamil_month: string; tamil_day: number;
  festivals: { key: string; name: string; name_en: string }[];
}
interface CalMonth {
  year: number; month: number; tradition: string; location: string;
  timezone: string; samvatsara: string; days: CalDay[]; note: string;
}

export default function CalendarPage() {
  const { t } = useLang();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [tradition, setTradition] = useState("telugu");
  const [location, setLocation] = useState("in");
  const [cal, setCal] = useState<CalMonth | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setBusy(true); setError("");
    try {
      const res = await fetch("/api/calendar", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ year, month, tradition, location }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("generic_error"));
      setCal(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setBusy(false);
    }
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [year, month, tradition, location]);

  function downloadICS() {
    if (!cal) return;
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
                   "PRODID:-//JyotishAI//Festival Calendar//EN"];
    for (const d of cal.days) {
      for (const f of d.festivals) {
        const dt = d.date.replaceAll("-", "");
        lines.push("BEGIN:VEVENT", `UID:${f.key}-${dt}@jyotishai`,
                   `DTSTART;VALUE=DATE:${dt}`,
                   `SUMMARY:${f.name_en}`,
                   `DESCRIPTION:${f.name} — ${d.tithi.name}, ${d.nakshatra.name} (${cal.location})`,
                   "END:VEVENT");
      }
    }
    lines.push("END:VCALENDAR");
    const blob = new Blob([lines.join("\r\n")], { type: "text/calendar" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `festivals-${cal.year}-${String(cal.month).padStart(2, "0")}.ics`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // Leading blanks so day 1 lands on its weekday column (Mon-first grid).
  const blanks = cal ? cal.days[0].weekday : 0;

  return (
    <main className="mx-auto max-w-6xl px-4 py-10 print:max-w-none print:px-2 print:py-2">
      <header className="mb-6 text-center print:mb-2">
        <h1 className="heading-display text-4xl print:text-2xl">{t("cal_title")}</h1>
        <div className="ornament mt-2 text-xs print:hidden">✦</div>
        {cal && (
          <p className="mt-2 text-sm text-[var(--ink-soft)]">
            {MONTHS[cal.month - 1]} {cal.year} · <span className="text-[var(--gold)]">{cal.samvatsara}</span>
            {" "}samvatsara · {cal.location} ({cal.timezone})
          </p>
        )}
      </header>

      {/* Controls — hidden in print */}
      <section className="card mb-6 flex flex-wrap items-end gap-3 p-4 print:hidden">
        <label className="text-sm">
          <span className="text-[var(--ink-muted)]">{t("cal_month")}</span>
          <select value={month} onChange={(e) => setMonth(+e.target.value)} className="input mt-1">
            {MONTHS.map((m, i) => <option key={m} value={i + 1}>{m}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="text-[var(--ink-muted)]">{t("cal_year")}</span>
          <select value={year} onChange={(e) => setYear(+e.target.value)} className="input mt-1">
            {Array.from({ length: 8 }, (_, i) => now.getFullYear() - 1 + i).map((y) =>
              <option key={y} value={y}>{y}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="text-[var(--ink-muted)]">{t("cal_tradition")}</span>
          <select value={tradition} onChange={(e) => setTradition(e.target.value)} className="input mt-1">
            {TRADITIONS.map((tr) => <option key={tr.key} value={tr.key}>{tr.label}</option>)}
          </select>
        </label>
        <label className="text-sm">
          <span className="text-[var(--ink-muted)]">{t("cal_location")}</span>
          <select value={location} onChange={(e) => setLocation(e.target.value)} className="input mt-1">
            {LOCATIONS.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
          </select>
        </label>
        <div className="ml-auto flex gap-2">
          <button onClick={() => window.print()} disabled={!cal} className="btn-gold text-sm">
            ⬇ {t("cal_download_pdf")}
          </button>
          <button onClick={downloadICS} disabled={!cal} className="btn-ghost text-sm">
            📅 {t("cal_download_ics")}
          </button>
        </div>
      </section>

      {busy && <p className="text-center text-sm text-[var(--ink-muted)]">{t("computing")}</p>}
      {error && <p className="text-center text-sm text-red-400">{error}</p>}

      {cal && !busy && (
        <>
          <div className="grid grid-cols-7 gap-1.5 print:gap-1">
            {WEEKDAYS.map((w, i) => (
              <div key={w} className={`pb-1 text-center text-xs font-semibold uppercase tracking-wider ${
                i === 6 ? "text-[var(--warn)]" : "text-[var(--ink-muted)]"}`}>
                {w}
              </div>
            ))}
            {Array.from({ length: blanks }).map((_, i) => <div key={`b${i}`} />)}
            {cal.days.map((d) => {
              const festive = d.festivals.length > 0;
              const sunday = d.weekday === 6;
              return (
                <div key={d.date}
                     className={`card min-h-[7.2rem] p-2 text-[11px] leading-tight print:min-h-[6rem] print:rounded print:p-1.5 ${
                       festive ? "border-[var(--line-gold)] shadow-[0_0_18px_-8px_rgba(217,171,46,0.5)]" : ""}`}>
                  <div className="flex items-baseline justify-between">
                    <span className={`font-display text-lg font-semibold ${
                      festive ? "text-[var(--gold)]" : sunday ? "text-[var(--warn)]" : "text-[var(--ink)]"}`}>
                      {d.day}
                    </span>
                    <span className="text-[9px] text-[var(--ink-faint)]">
                      {tradition === "tamil"
                        ? `${d.tamil_month} ${d.tamil_day}`
                        : `${d.masa_adhika ? "Adhika " : ""}${d.masa}`}
                    </span>
                  </div>
                  <div className="mt-1 text-[var(--ink-soft)]">
                    {d.tithi.name}
                    {d.tithi.ends && <span className="text-[var(--ink-faint)]"> →{d.tithi.ends}</span>}
                  </div>
                  <div className="text-[var(--ink-muted)]">
                    {d.nakshatra.name}
                    {d.nakshatra.ends && <span className="text-[var(--ink-faint)]"> →{d.nakshatra.ends}</span>}
                  </div>
                  <div className="mt-0.5 text-[9px] text-[var(--ink-faint)]">
                    ☀ {d.sunrise}–{d.sunset}
                  </div>
                  {d.festivals.map((f) => (
                    <div key={f.key}
                         className="mt-1 rounded bg-[var(--gold)]/15 px-1.5 py-0.5 font-semibold text-[var(--gold)]">
                      ✦ {f.name}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
          <p className="mt-4 text-center text-[10px] text-[var(--ink-faint)] print:mt-2">
            {cal.note}
          </p>
        </>
      )}
    </main>
  );
}
