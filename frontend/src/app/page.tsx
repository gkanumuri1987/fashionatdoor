"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { NorthChart, SouthChart } from "@/components/KundliCharts";
import { DashaTimeline, PanchangaYogas, PlanetTable } from "@/components/ChartDetails";
import AuthBar from "@/components/AuthBar";
import SavedProfiles, { type BirthProfile } from "@/components/SavedProfiles";
import type { ChartV1 } from "@/lib/types";
import { LangSwitcher, useLang } from "@/lib/i18n";
import { copyText } from "@/lib/clipboard";

interface Place { name: string; lat: number; lng: number }

const TABS = ["Chart", "Planets", "Dasha", "Panchanga", "Reading"] as const;

const READING_SECTIONS: [string, string][] = [
  ["personality", "Personality"], ["career", "Career"], ["wealth", "Wealth"],
  ["relationships", "Relationships"], ["health", "Health"], ["dharma", "Dharma"],
  ["dasha_outlook", "Current Period"], ["remedies", "Remedies"],
];

export default function Home() {
  const { lang, t } = useLang();
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
  const [readingBusy, setReadingBusy] = useState(false);
  const [readingError, setReadingError] = useState("");
  const [palmLink, setPalmLink] = useState("");
  const [palmCopied, setPalmCopied] = useState<null | boolean>(null);
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  async function fetchReading(section: string) {
    if (!chart) return;
    const key = `${section}:${lang}`;
    setReadingSection(section);
    if (readings[key]) return;
    setReadingBusy(true); setReadingError("");
    try {
      const res = await fetch("/api/reading", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart, section, language: lang }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Reading failed");
      setReadings((r) => ({ ...r, [key]: data.text }));
    } catch (e) {
      setReadingError(e instanceof Error ? e.message : t("generic_error"));
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
      setPalmCopied(await copyText(url) ? true : null);
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
      setError(t("pick_place"));
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
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <div className="mb-2 flex items-center justify-end gap-3">
        <LangSwitcher />
        <AuthBar />
      </div>
      <header className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-[#c9a227]">{t("app_title")}</h1>
        <p className="mt-1 text-sm text-[#9c8f6f]">
{t("tagline")}</p>
        <nav className="mt-3 flex items-center justify-center gap-4 text-sm">
          <span className="font-semibold text-[#c9a227]">{t("nav_kundli")}</span>
          <Link href="/match" className="text-[#cbbfa4] hover:text-[#c9a227]">{t("nav_milan")}</Link>
          <button onClick={mintPalmLink} className="text-[#cbbfa4] hover:text-[#c9a227]">
{t("nav_palm")}</button>
        </nav>
        {palmLink && (
          <div className="mx-auto mt-3 max-w-xl rounded-lg border border-[#3d2f5c] bg-[#1a1030]/60 p-3 text-xs">
            <span className="text-[#9c8f6f]">{t("share_link")} </span>
            <code className="break-all text-[#c9a227]">{palmLink}</code>
            <div className="mt-2 flex flex-wrap justify-center gap-2">
              <button
                onClick={async () => setPalmCopied(await copyText(palmLink))}
                className="rounded-md bg-[#c9a227] px-3 py-1 font-semibold text-[#140b26] hover:bg-[#dcb63a]"
              >
                {palmCopied ? t("copied") : t("copy")}
              </button>
              <a
                href={`https://wa.me/?text=${encodeURIComponent(`${t("palm_share_msg")} ${palmLink}`)}`}
                target="_blank" rel="noopener noreferrer"
                className="rounded-md border border-[#25D366] px-3 py-1 text-[#25D366] hover:bg-[#25D366]/10"
              >
                {t("share_whatsapp")}
              </a>
              {typeof navigator !== "undefined" && "share" in navigator && (
                <button
                  onClick={() => navigator.share({ text: t("palm_share_msg"), url: palmLink }).catch(() => {})}
                  className="rounded-md border border-[#3d2f5c] px-3 py-1 text-[#cbbfa4] hover:bg-[#2a1d45]"
                >
                  {t("share_native")}
                </button>
              )}
            </div>
            {palmCopied === false && <p className="mt-1 text-orange-300">{t("copy_failed")}</p>}
          </div>
        )}
      </header>

      <section className="rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-sm">
            <span className="text-[#9c8f6f]">{t("dob")}</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                   className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2" />
          </label>
          <label className="block text-sm">
            <span className="text-[#9c8f6f]">{t("tob")}</span>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)}
                   className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2" />
            <select value={timeAccuracy} onChange={(e) => setTimeAccuracy(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-2 py-1 text-xs">
              <option value="exact">{t("time_exact")}</option>
              <option value="approximate">{t("time_approx")}</option>
              <option value="unknown">{t("time_unknown")}</option>
            </select>
          </label>
          <label className="relative block text-sm">
            <span className="text-[#9c8f6f]">{t("pob")}</span>
            <input
              value={placeQuery}
              onChange={(e) => { setPlaceQuery(e.target.value); setPlace(null); }}
              placeholder={t("place_ph")}
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
            <span className="text-[#9c8f6f]">{t("ayanamsa")}</span>
            <select value={ayanamsa} onChange={(e) => setAyanamsa(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2">
              <option value="lahiri">Lahiri (Chitrapaksha)</option>
              <option value="raman">Raman</option>
              <option value="kp">KP (Krishnamurti)</option>
            </select>
          </label>
        </div>
        {timeAccuracy !== "exact" && (
          <p className="mt-3 text-xs text-orange-300">{t("accuracy_warning")}</p>
        )}
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={generate}
            disabled={loading}
            className="rounded-lg bg-[#c9a227] px-5 py-2 font-semibold text-[#140b26] hover:bg-[#dcb63a] disabled:opacity-50"
          >
            {loading ? t("computing") : t("generate")}
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
              {t("lagna")} <span className="text-[#ede6d6]">{chart.lagna.sign_name} {chart.lagna.degree_in_sign}</span>
              {" · "}{t("moon")} <span className="text-[#ede6d6]">{chart.moon_sign_name}</span>
              {" · "}{chart.input.tz} (UTC{chart.input.utc_offset_hours >= 0 ? "+" : ""}{chart.input.utc_offset_hours})
              {" · "}{t("ayanamsa")} {chart.ayanamsa_value.toFixed(4)}°
            </div>
            <nav className="flex gap-1 rounded-lg border border-[#3d2f5c] p-1 text-sm">
              {TABS.map((tb) => (
                <button key={tb} onClick={() => setTab(tb)}
                        className={`rounded-md px-3 py-1 ${tab === tb ? "bg-[#c9a227] font-semibold text-[#140b26]" : "text-[#cbbfa4]"}`}>
                  {t(`tab_${tb.toLowerCase()}`)}
                </button>
              ))}
            </nav>
          </div>

          {tab === "Chart" && (
            <div>
              <div className="mb-3 flex gap-1 text-xs">
                {(["south", "north"] as const).map((s) => (
                  <button key={s} onClick={() => setStyle(s)}
                          className={`rounded-md border border-[#3d2f5c] px-3 py-1 ${style === s ? "bg-[#3d2f5c]" : ""}`}>
                    {t(`${s}_indian`)}
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
                {READING_SECTIONS.map(([key]) => (
                  <button key={key} onClick={() => fetchReading(key)}
                          className={`rounded-full border px-3 py-1 text-xs ${
                            readingSection === key
                              ? "border-[#c9a227] bg-[#c9a227]/15 text-[#c9a227]"
                              : "border-[#3d2f5c] text-[#cbbfa4]"}`}>
                    {t(`sec_${key}`)}
                  </button>
                ))}
              </div>
              {readingBusy && <p className="text-sm text-[#9c8f6f]">{t("consulting")}</p>}
              {readingError && <p className="text-sm text-red-400">{readingError}</p>}
              {readings[`${readingSection}:${lang}`] ? (
                <div className="whitespace-pre-wrap rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-sm leading-relaxed">
                  {readings[`${readingSection}:${lang}`]}
                </div>
              ) : (!readingBusy && !readingError && (
                <p className="text-sm text-[#9c8f6f]">{t("reading_hint")}</p>
              ))}
            </div>
          )}
        </section>
      )}

      <footer className="mt-12 text-center text-xs text-[#9c8f6f]">{t("disclaimer")}</footer>
    </main>
  );
}
