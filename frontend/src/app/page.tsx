"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { NorthChart, SouthChart } from "@/components/KundliCharts";
import { DashaTimeline, PanchangaYogas, PlanetTable } from "@/components/ChartDetails";
import AuthBar from "@/components/AuthBar";
import SavedProfiles, { type BirthProfile } from "@/components/SavedProfiles";
import type { ChartV1 } from "@/lib/types";

interface Place { name: string; lat: number; lng: number }

const TABS = ["Chart", "Planets", "Dasha", "Panchanga", "Reading"] as const;

const READING_SECTIONS: [string, string][] = [
  ["personality", "Personality"], ["career", "Career"], ["wealth", "Wealth"],
  ["relationships", "Relationships"], ["health", "Health"], ["dharma", "Dharma"],
  ["dasha_outlook", "Current Period"], ["remedies", "Remedies"],
];

export default function Home() {
  const [date, setDate] = useState("1990-05-15");
  const [time, setTime] = useState("10:30");
  const [timeAccuracy, setTimeAccuracy] = useState("exact");
  const [placeQuery, setPlaceQuery] = useState("");
  const [places, setPlaces] = useState<Place[]>([]);
  const [place, setPlace] = useState<Place | null>(null);
  const [ayanamsa, setAyanamsa] = useState("lahiri");
  const [chart, setChart] = useState<ChartV1 | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState<(typeof TABS)[number]>("Chart");
  const [style, setStyle] = useState<"north" | "south">("south");
  const [readings, setReadings] = useState<Record<string, string>>({});
  const [readingSection, setReadingSection] = useState("personality");
  const [readingLang, setReadingLang] = useState("en");
  const [readingBusy, setReadingBusy] = useState(false);
  const [readingError, setReadingError] = useState("");
  const [palmLink, setPalmLink] = useState("");
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  async function fetchReading(section: string) {
    if (!chart) return;
    const key = `${section}:${readingLang}`;
    setReadingSection(section);
    if (readings[key]) return;
    setReadingBusy(true); setReadingError("");
    try {
      const res = await fetch("/api/reading", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart, section, language: readingLang }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Reading failed");
      setReadings((r) => ({ ...r, [key]: data.text }));
    } catch (e) {
      setReadingError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setReadingBusy(false);
    }
  }

  async function mintPalmLink() {
    try {
      const res = await fetch("/api/palm/sessions", { method: "POST" });
      const data = await res.json();
      const url = `${window.location.origin}${data.path}`;
      setPalmLink(url);
      try { await navigator.clipboard.writeText(url); } catch { /* shown below anyway */ }
    } catch {
      setPalmLink("");
    }
  }

  useEffect(() => {
    if (placeQuery.trim().length < 3 || (place && placeQuery === place.name)) {
      setPlaces([]);
      return;
    }
    clearTimeout(debounce.current);
    debounce.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/geocode?q=${encodeURIComponent(placeQuery)}`);
        if (res.ok) setPlaces(await res.json());
      } catch {
        /* best-effort autocomplete */
      }
    }, 400);
    return () => clearTimeout(debounce.current);
  }, [placeQuery, place]);

  async function generate() {
    if (!place) {
      setError("Pick a birth place from the suggestions.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/chart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date, time, lat: place.lat, lng: place.lng,
          ayanamsa, time_accuracy: timeAccuracy,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chart computation failed");
      setChart(data);
      setTab("Chart");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-2 flex justify-end">
        <AuthBar />
      </div>
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-[#c9a227]">Jyotish AI</h1>
        <p className="mt-1 text-sm text-[#9c8f6f]">
          Vedic birth chart — computed with Swiss Ephemeris, never guessed by AI
        </p>
        <nav className="mt-3 flex items-center justify-center gap-4 text-sm">
          <span className="font-semibold text-[#c9a227]">Kundli</span>
          <Link href="/match" className="text-[#cbbfa4] hover:text-[#c9a227]">Kundli Milan</Link>
          <button onClick={mintPalmLink} className="text-[#cbbfa4] hover:text-[#c9a227]">
            Palmistry link
          </button>
        </nav>
        {palmLink && (
          <div className="mx-auto mt-3 max-w-xl rounded-lg border border-[#3d2f5c] bg-[#1a1030]/60 p-3 text-xs">
            <span className="text-[#9c8f6f]">Share this link (copied; valid 48h): </span>
            <code className="break-all text-[#c9a227]">{palmLink}</code>
          </div>
        )}
      </header>

      <section className="rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-sm">
            <span className="text-[#9c8f6f]">Date of birth</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                   className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2" />
          </label>
          <label className="block text-sm">
            <span className="text-[#9c8f6f]">Time of birth</span>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)}
                   className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2" />
            <select value={timeAccuracy} onChange={(e) => setTimeAccuracy(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-2 py-1 text-xs">
              <option value="exact">Time is exact</option>
              <option value="approximate">Approximate (±30 min)</option>
              <option value="unknown">Unknown</option>
            </select>
          </label>
          <label className="relative block text-sm">
            <span className="text-[#9c8f6f]">Place of birth</span>
            <input
              value={placeQuery}
              onChange={(e) => { setPlaceQuery(e.target.value); setPlace(null); }}
              placeholder="City, country…"
              className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2"
            />
            {places.length > 0 && (
              <ul className="absolute z-10 mt-1 max-h-52 w-full overflow-auto rounded-lg border border-[#3d2f5c] bg-[#241640] text-xs shadow-xl">
                {places.map((p) => (
                  <li key={p.name}>
                    <button
                      className="w-full px-3 py-2 text-left hover:bg-[#c9a227]/10"
                      onClick={() => { setPlace(p); setPlaceQuery(p.name); setPlaces([]); }}
                    >
                      {p.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </label>
          <label className="block text-sm">
            <span className="text-[#9c8f6f]">Ayanamsa</span>
            <select value={ayanamsa} onChange={(e) => setAyanamsa(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2">
              <option value="lahiri">Lahiri (Chitrapaksha)</option>
              <option value="raman">Raman</option>
              <option value="kp">KP (Krishnamurti)</option>
            </select>
          </label>
        </div>
        {timeAccuracy !== "exact" && (
          <p className="mt-3 text-xs text-orange-300">
            The ascendant moves a full sign roughly every 2 hours — with an{" "}
            {timeAccuracy === "unknown" ? "unknown" : "approximate"} birth time, lagna-based
            results (houses, dasha timing) carry uncertainty.
          </p>
        )}
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={generate}
            disabled={loading}
            className="rounded-lg bg-[#c9a227] px-5 py-2 font-semibold text-[#140b26] hover:bg-[#dcb63a] disabled:opacity-50"
          >
            {loading ? "Computing…" : "Generate Kundli"}
          </button>
          {error && <span className="text-sm text-red-400">{error}</span>}
        </div>
      </section>
      <SavedProfiles
        draft={place ? {
          name: "", birth_date: date, birth_time: time, time_accuracy: timeAccuracy,
          place_name: place.name, lat: place.lat, lng: place.lng, ayanamsa,
        } : null}
        onLoad={(p: BirthProfile) => {
          setDate(p.birth_date);
          setTime(p.birth_time.slice(0, 5));
          setTimeAccuracy(p.time_accuracy);
          setAyanamsa(p.ayanamsa);
          setPlace({ name: p.place_name, lat: p.lat, lng: p.lng });
          setPlaceQuery(p.place_name);
          setChart(null);
        }}
      />


      {chart && (
        <section className="mt-8">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div className="text-sm text-[#9c8f6f]">
              Lagna <span className="text-[#ede6d6]">{chart.lagna.sign_name} {chart.lagna.degree_in_sign}</span>
              {" · "}Moon <span className="text-[#ede6d6]">{chart.moon_sign_name}</span>
              {" · "}{chart.input.tz} (UTC{chart.input.utc_offset_hours >= 0 ? "+" : ""}{chart.input.utc_offset_hours})
              {" · "}Ayanamsa {chart.ayanamsa_value.toFixed(4)}°
            </div>
            <nav className="flex gap-1 rounded-lg border border-[#3d2f5c] p-1 text-sm">
              {TABS.map((t) => (
                <button key={t} onClick={() => setTab(t)}
                        className={`rounded-md px-3 py-1 ${tab === t ? "bg-[#c9a227] font-semibold text-[#140b26]" : "text-[#cbbfa4]"}`}>
                  {t}
                </button>
              ))}
            </nav>
          </div>

          {tab === "Chart" && (
            <div>
              <div className="mb-3 flex gap-1 text-xs">
                {(["south", "north"] as const).map((s) => (
                  <button key={s} onClick={() => setStyle(s)}
                          className={`rounded-md border border-[#3d2f5c] px-3 py-1 capitalize ${style === s ? "bg-[#3d2f5c]" : ""}`}>
                    {s} Indian
                  </button>
                ))}
              </div>
              <div className="flex justify-center rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-6">
                {style === "south" ? <SouthChart chart={chart} /> : <NorthChart chart={chart} />}
              </div>
            </div>
          )}
          {tab === "Planets" && <PlanetTable chart={chart} />}
          {tab === "Dasha" && <DashaTimeline chart={chart} />}
          {tab === "Panchanga" && <PanchangaYogas chart={chart} />}
          {tab === "Reading" && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                {READING_SECTIONS.map(([key, label]) => (
                  <button key={key} onClick={() => fetchReading(key)}
                          className={`rounded-full border px-3 py-1 text-xs ${
                            readingSection === key
                              ? "border-[#c9a227] bg-[#c9a227]/15 text-[#c9a227]"
                              : "border-[#3d2f5c] text-[#cbbfa4]"}`}>
                    {label}
                  </button>
                ))}
                <select value={readingLang}
                        onChange={(e) => setReadingLang(e.target.value)}
                        className="ml-auto rounded-lg border border-[#3d2f5c] bg-[#140b26] px-2 py-1 text-xs">
                  <option value="en">English</option>
                  <option value="te">తెలుగు</option>
                  <option value="hi">हिन्दी</option>
                </select>
              </div>
              {readingBusy && <p className="text-sm text-[#9c8f6f]">Consulting the classics…</p>}
              {readingError && <p className="text-sm text-red-400">{readingError}</p>}
              {readings[`${readingSection}:${readingLang}`] ? (
                <div className="whitespace-pre-wrap rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-sm leading-relaxed">
                  {readings[`${readingSection}:${readingLang}`]}
                </div>
              ) : (!readingBusy && !readingError && (
                <p className="text-sm text-[#9c8f6f]">
                  Pick a section — the reading is written from your computed chart and
                  classical dictums (BPHS, Phaladeepika, Saravali, Puranic archetypes).
                </p>
              ))}
            </div>
          )}
        </section>
      )}

      <footer className="mt-12 text-center text-xs text-[#9c8f6f]">
        For guidance and reflection — not a substitute for professional advice.
      </footer>
    </main>
  );
}
