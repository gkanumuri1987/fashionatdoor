"use client";

import { useEffect, useRef, useState } from "react";
import { NorthChart, SouthChart } from "@/components/KundliCharts";
import { DashaTimeline, PanchangaYogas, PlanetTable } from "@/components/ChartDetails";
import SavedProfiles, { type BirthProfile } from "@/components/SavedProfiles";
import type { ChartV1, ReadingPage } from "@/lib/types";
import { useLang } from "@/lib/i18n";

interface Place { name: string; lat: number; lng: number }

const SIGN_NAMES = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
                    "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];

const TABS = ["Chart", "Planets", "Dasha", "Panchanga", "Advanced", "Reading"] as const;

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
  const [dashaSystem, setDashaSystem] = useState<"vimshottari" | "yogini" | "ashtottari" | "kalachakra" | "narayana">("vimshottari");
  const [altDashas, setAltDashas] = useState<Record<string, {lord?: string; yogini?: string; sign_name?: string; years: number; start: string; end: string}[]>>({});
  const [dashaBusy, setDashaBusy] = useState(false);
  const [page, setPage] = useState<ReadingPage | null>(null);
  const [showAyInfo, setShowAyInfo] = useState(false);
  const [showWhy, setShowWhy] = useState(false);
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

  async function pickDashaSystem(sys: "vimshottari" | "yogini" | "ashtottari" | "kalachakra" | "narayana") {
    setDashaSystem(sys);
    if (sys === "vimshottari" || altDashas[sys] || !chart) return;
    setDashaBusy(true);
    try {
      const res = await fetch("/api/dashas", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart, system: sys }),
      });
      const data = await res.json();
      if (res.ok) setAltDashas((a) => ({ ...a, [sys]: data.mahadashas }));
    } catch { /* selector falls back to vimshottari view */ }
    finally { setDashaBusy(false); }
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
      fetch("/api/reading-page", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart: data, language: lang }),
      }).then((r) => (r.ok ? r.json() : null)).then(setPage).catch(() => setPage(null));
      setAltDashas({});
      setDashaSystem("vimshottari");
      setTab("Chart");
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="heading-display text-5xl">{t("app_title")}</h1>
        <div className="ornament mt-2 text-xs">✦</div>
        <p className="mt-1 text-sm text-[var(--ink-muted)]">
{t("tagline")}</p>
      </header>

      <section className="card p-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-sm">
            <span className="text-[var(--ink-muted)]">{t("dob")}</span>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)}
                   className="input mt-1" />
          </label>
          <label className="block text-sm">
            <span className="text-[var(--ink-muted)]">{t("tob")}</span>
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)}
                   className="input mt-1" />
            <select value={timeAccuracy} onChange={(e) => setTimeAccuracy(e.target.value)}
                    className="input mt-1 px-2 py-1 text-xs">
              <option value="exact">{t("time_exact")}</option>
              <option value="approximate">{t("time_approx")}</option>
              <option value="unknown">{t("time_unknown")}</option>
            </select>
          </label>
          <label className="relative block text-sm">
            <span className="text-[var(--ink-muted)]">{t("pob")}</span>
            <input
              value={placeQuery}
              onChange={(e) => { setPlaceQuery(e.target.value); setPlace(null); }}
              placeholder={t("place_ph")}
              className="input mt-1"
            />
            {places.length > 0 && (
              <ul className="absolute z-10 mt-1 max-h-52 w-full overflow-auto rounded-lg border border-[var(--line)] bg-[var(--surface-raised)] text-xs shadow-xl">
                {places.map((p) => (
                  <li key={p.name}>
                    <button
                      className="w-full px-3 py-2 text-left hover:bg-[var(--gold)]/10"
                      onClick={() => { setPlace(p); setPlaceQuery(p.name); setPlaces([]); }}
                    >
                      {p.name}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </label>
          <label className="relative block text-sm">
            <span className="flex items-center gap-1.5 text-[var(--ink-muted)]">
              {t("ayanamsa")}
              <button type="button" onClick={(e) => { e.preventDefault(); setShowAyInfo((v) => !v); }}
                      aria-label={t("ay_info_title")}
                      className="flex h-4 w-4 items-center justify-center rounded-full border border-[var(--line)] text-[10px] text-[var(--gold)] hover:border-[var(--line-gold)]">
                i
              </button>
            </span>
            <select value={ayanamsa} onChange={(e) => setAyanamsa(e.target.value)}
                    className="input mt-1">
              <option value="lahiri">Lahiri (Chitrapaksha) ★ {t("recommended")}</option>
              <option value="raman">Raman</option>
              <option value="kp">KP (Krishnamurti)</option>
            </select>
            {showAyInfo && (
              <div className="card absolute right-0 top-full z-20 mt-2 w-80 p-4 text-xs leading-relaxed"
                   onClick={(e) => e.preventDefault()}>
                <div className="mb-1 flex items-start justify-between">
                  <b className="text-[var(--gold)]">{t("ay_info_title")}</b>
                  <button type="button" onClick={(e) => { e.preventDefault(); setShowAyInfo(false); }}
                          className="text-[var(--ink-muted)]">✕</button>
                </div>
                <p className="text-[var(--ink-soft)]">{t("ay_info_body")}</p>
                <ul className="mt-2 space-y-1.5">
                  <li><b className="text-[var(--gold)]">★ Lahiri</b> — <span className="text-[var(--ink-soft)]">{t("ay_lahiri")}</span></li>
                  <li><b className="text-[var(--ink)]">Raman</b> — <span className="text-[var(--ink-soft)]">{t("ay_raman")}</span></li>
                  <li><b className="text-[var(--ink)]">KP</b> — <span className="text-[var(--ink-soft)]">{t("ay_kp")}</span></li>
                </ul>
                <p className="mt-2 border-t border-[var(--line-soft)] pt-2 text-[var(--good)]">
                  ✓ {t("ay_recommend")}
                </p>
              </div>
            )}
          </label>
        </div>
        {timeAccuracy !== "exact" && (
          <p className="mt-3 text-xs text-orange-300">{t("accuracy_warning")}</p>
        )}
        <div className="mt-4 flex items-center gap-3">
          <button
            onClick={generate}
            disabled={loading}
            className="btn-gold"
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
            <div className="text-sm text-[var(--ink-muted)]">
              {t("lagna")} <span className="text-[var(--ink)]">{chart.lagna.sign_name} {chart.lagna.degree_in_sign}</span>
              {" · "}{t("moon")} <span className="text-[var(--ink)]">{chart.moon_sign_name}</span>
              {" · "}{chart.input.tz} (UTC{chart.input.utc_offset_hours >= 0 ? "+" : ""}{chart.input.utc_offset_hours})
              {" · "}{t("ayanamsa")} {chart.ayanamsa_value.toFixed(4)}°
            </div>
            <nav className="flex gap-1 rounded-lg border border-[var(--line)] p-1 text-sm">
              {TABS.map((tb) => (
                <button key={tb} onClick={() => setTab(tb)}
                        className={`pill ${tab === tb ? "pill-active" : ""}`}>
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
                          className={`rounded-md border border-[var(--line)] px-3 py-1 ${style === s ? "bg-[var(--surface-raised)]" : ""}`}>
                    {t(`${s}_indian`)}
                  </button>
                ))}
              </div>
              <div className="card flex justify-center p-6">
                {style === "south" ? <SouthChart chart={chart} /> : <NorthChart chart={chart} />}
              </div>
            </div>
          )}
          {tab === "Planets" && <PlanetTable chart={chart} />}
          {tab === "Dasha" && (
            <div>
              <div className="mb-3 flex items-center gap-2 text-xs">
                <span className="text-[var(--ink-muted)]">{t("dasha_system")}:</span>
                {(["vimshottari", "yogini", "ashtottari", "kalachakra", "narayana"] as const).map((sys) => (
                  <button key={sys} onClick={() => pickDashaSystem(sys)}
                          className={`rounded-md border border-[var(--line)] px-3 py-1 capitalize ${dashaSystem === sys ? "bg-[var(--surface-raised)]" : ""}`}>
                    {sys}
                  </button>
                ))}
              </div>
              {dashaSystem === "vimshottari" ? (
                <div>
                  {page?.timeline?.current_sentence && (
                    <p className="mb-3 rounded-lg border border-[var(--line-gold)] bg-[var(--gold)]/10 px-3 py-2 text-sm text-[var(--gold-bright)]">
                      📍 {page.timeline.current_sentence}
                    </p>
                  )}
                  <DashaTimeline chart={chart} />
                </div>
              ) : dashaBusy ? (
                <p className="text-sm text-[var(--ink-muted)]">{t("loading_dasha")}</p>
              ) : altDashas[dashaSystem] ? (
                <div className="overflow-x-auto rounded-lg border border-[var(--line)]">
                  <table className="w-full text-sm">
                    <thead><tr className="bg-[var(--surface-raised)] text-left text-[var(--gold)]">
                      <th className="px-3 py-2">{dashaSystem === "yogini" ? "Yogini" : (dashaSystem === "kalachakra" || dashaSystem === "narayana") ? "Rashi" : "Lord"}</th>
                      <th className="px-3 py-2">Years</th>
                      <th className="px-3 py-2">Start</th><th className="px-3 py-2">End</th>
                    </tr></thead>
                    <tbody>
                      {altDashas[dashaSystem].map((m, i) => (
                        <tr key={i} className="border-t border-[var(--line-soft)]">
                          <td className="px-3 py-2 capitalize">{m.yogini ? `${m.yogini} (${m.lord})` : (m.sign_name ?? m.lord)}</td>
                          <td className="px-3 py-2">{m.years}</td>
                          <td className="px-3 py-2">{m.start.slice(0, 10)}</td>
                          <td className="px-3 py-2">{m.end.slice(0, 10)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-[var(--ink-muted)]">{t("generic_error")}</p>
              )}
            </div>
          )}
          {tab === "Panchanga" && <PanchangaYogas chart={chart} />}
          {tab === "Advanced" && (
            <div className="space-y-5 text-sm">
              {chart.jaimini && (
                <div className="card p-5">
                  <h3 className="heading-section mb-3 text-lg">{t("jaimini_title")}</h3>
                  <div className="mb-3 grid gap-2 sm:grid-cols-2">
                    <div className="rounded-lg border border-[var(--line)] p-3">
                      <div className="text-xs text-[var(--ink-muted)]">{t("ishta_devata")}</div>
                      <div className="mt-1 text-[var(--ink)]">
                        {chart.jaimini.ishta_devata?.deity}
                        <span className="ml-1 text-xs text-[var(--ink-muted)]">
                          (via {chart.jaimini.ishta_devata?.indicator_graha})
                        </span>
                      </div>
                    </div>
                    <div className="rounded-lg border border-[var(--line)] p-3">
                      <div className="text-xs text-[var(--ink-muted)]">{t("arudha_lagna")} / {t("upapada")}</div>
                      <div className="mt-1 text-[var(--ink)]">
                        AL: {SIGN_NAMES[chart.jaimini.arudha_padas?.AL ?? 0]} · UL: {SIGN_NAMES[chart.jaimini.arudha_padas?.UL ?? 0]}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-[var(--ink-muted)]">{t("chara_karakas")}</div>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {Object.entries(chart.jaimini.chara_karakas?.karakas ?? {}).map(([role, k]) => (
                      <span key={role} className="rounded-full border border-[var(--line)] px-2 py-0.5 text-xs">
                        <b className="text-[var(--gold)]">{role}</b>{" "}
                        <span className="capitalize">{(k as {graha: string}).graha}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {chart.kp && (
                <div className="card p-5">
                  <h3 className="heading-section mb-3 text-lg">{t("kp_title")}</h3>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="text-left text-[var(--gold)]">
                        <th className="px-2 py-1">Graha</th><th className="px-2 py-1">Star lord</th>
                        <th className="px-2 py-1">Sub</th><th className="px-2 py-1">Sub-sub</th>
                      </tr></thead>
                      <tbody>
                        {Object.entries(chart.kp.planets ?? {}).map(([g, e]) => {
                          const kp = e as {star_lord: string; sub_lord: string; sub_sub_lord: string};
                          return (
                            <tr key={g} className="border-t border-[var(--line-soft)] capitalize">
                              <td className="px-2 py-1">{g}</td><td className="px-2 py-1">{kp.star_lord}</td>
                              <td className="px-2 py-1">{kp.sub_lord}</td><td className="px-2 py-1">{kp.sub_sub_lord}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              {chart.bhava_chalita && (
                <div className="card p-5">
                  <h3 className="heading-section mb-3 text-lg">{t("bhava_chalita_title")}</h3>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {Object.entries(chart.bhava_chalita.grahas ?? {}).map(([g, m]) => {
                      const mem = m as {house: number; in_sandhi: boolean};
                      const rasiHouse = chart.grahas[g]?.house;
                      const moved = rasiHouse !== undefined && rasiHouse !== mem.house;
                      return (
                        <span key={g} className={`rounded-full border px-2 py-0.5 capitalize ${moved ? "border-[var(--gold)] text-[var(--gold)]" : "border-[var(--line)]"}`}>
                          {g}: {mem.house}{moved ? ` (rasi ${rasiHouse})` : ""}{mem.in_sandhi ? " ⚠" : ""}
                        </span>
                      );
                    })}
                  </div>
                  <p className="mt-2 text-xs text-[var(--ink-muted)]">⚠ = {t("in_sandhi")}</p>
                </div>
              )}
            </div>
          )}
          {tab === "Reading" && (
            <div className="space-y-4">
              {page && (
                <div className="space-y-2">
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(page.verdicts ?? {}).map(([topic, v]) => (
                      <span key={topic}
                            className={`rounded-full border px-3 py-1 text-xs capitalize ${
                              v.verdict === "supportive" ? "border-emerald-500/50 text-emerald-300" :
                              v.verdict === "challenging" ? "border-orange-500/50 text-orange-300" :
                              "border-[var(--line)] text-[var(--ink-soft)]"}`}>
                        {t(`sec_${topic}`) !== `sec_${topic}` ? t(`sec_${topic}`) : topic}: {t(`verdict_${v.verdict}`)}
                      </span>
                    ))}
                  </div>
                  {(page.uncertainty ?? []).map((n, i) => (
                    <p key={i} className="text-xs text-orange-300/90">⚠ {n}</p>
                  ))}
                  <button onClick={() => setShowWhy((w) => !w)}
                          className="text-xs text-[var(--gold)] underline">
                    {t("why_receipts")}
                  </button>
                  {showWhy && (
                    <div className="max-h-72 space-y-2 overflow-y-auto rounded-lg border border-[var(--line)] bg-[var(--surface-deep)] p-3 text-xs">
                      {(page.claims ?? []).map((c) => (
                        <div key={c.id} className="border-b border-[var(--line-soft)] pb-1">
                          <div className="text-[var(--ink)]">{c.claim}</div>
                          <div className="text-[var(--ink-muted)]">
                            {c.chart_condition} · {c.source} · <b>{c.strength}</b>
                            {c.cancellations.length > 0 && (
                              <span className="text-emerald-400"> · cancelled: {c.cancellations.join("; ")}</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
              <div className="flex flex-wrap items-center gap-2">
                {READING_SECTIONS.map(([key]) => (
                  <button key={key} onClick={() => fetchReading(key)}
                          className={`rounded-full border px-3 py-1 text-xs ${
                            readingSection === key
                              ? "border-[var(--gold)] bg-[var(--gold)]/15 text-[var(--gold)]"
                              : "border-[var(--line)] text-[var(--ink-soft)]"}`}>
                    {t(`sec_${key}`)}
                  </button>
                ))}
              </div>
              {readingBusy && <p className="text-sm text-[var(--ink-muted)]">{t("consulting")}</p>}
              {readingError && <p className="text-sm text-red-400">{readingError}</p>}
              {readings[`${readingSection}:${lang}`] ? (
                <div className="card whitespace-pre-wrap p-5 text-sm leading-relaxed">
                  {readings[`${readingSection}:${lang}`]}
                </div>
              ) : (!readingBusy && !readingError && (
                <p className="text-sm text-[var(--ink-muted)]">{t("reading_hint")}</p>
              ))}
            </div>
          )}
        </section>
      )}

      <footer className="mt-12 text-center text-xs text-[var(--ink-muted)]">{t("disclaimer")}</footer>
    </main>
  );
}
