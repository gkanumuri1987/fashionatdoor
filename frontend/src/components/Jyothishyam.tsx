"use client";

/** Personal Jyothishyam panel — today + week, computed from panchanga (never
 *  AI-imagined). Plus / Lifetime Plus feature; others see the upgrade path.
 *  Interests let the person track career / relationship / health etc. */

import { useCallback, useEffect, useState } from "react";
import { chatUnlimited, useAccount } from "@/lib/account";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";
import type { ChartV1 } from "@/lib/types";
import { resolveTiming } from "@/lib/locations";

const INTERESTS = ["career", "relationship", "health", "finance", "education", "spiritual"];

interface Day {
  date: string; weekday: string; vara_deity: string; day_affairs: string;
  tithi: { name: string; group: string; note: string };
  nakshatra: { name: string; class: string; supports: string };
  yoga: string;
  tarabala: { name: string; favourable: boolean; note: string };
  chandrabala: { house: number; favourable: boolean };
  new_ventures: string; continuations: string;
  cautions: string[]; rahu_kalam: string | null;
  focus: { interest: string; about: string; note: string }[];
}
interface Forecast {
  today: Day; week: Day[];
  week_highlights: { good_days: string[]; careful_days: string[] };
  period: { maha_lord: string; week_deity: string; week_remedy: string;
            antar_lord: string; antar_deity: string; antar_remedy: string };
  note: string;
}

const VERDICT_COLOR: Record<string, string> = {
  favourable: "text-[var(--good)]", smooth: "text-[var(--good)]",
  mixed: "text-[var(--warn)]", "push through": "text-[var(--warn)]",
  avoid: "text-[var(--bad)]", "go slow": "text-[var(--bad)]",
};

export default function Jyothishyam({ chart }: { chart: ChartV1 }) {
  const { t } = useLang();
  const sb = supabase();
  const { account, signedIn } = useAccount();
  const [interests, setInterests] = useState<string[]>([]);
  const [residence, setResidence] = useState<string | null>(null);
  const [fc, setFc] = useState<Forecast | null>(null);
  const [busy, setBusy] = useState(false);
  const [view, setView] = useState<"today" | "week">("today");

  const premium = chatUnlimited(account);

  // Load saved interests from user metadata.
  useEffect(() => {
    if (!sb) return;
    sb.auth.getUser().then(({ data }) => {
      const saved = (data.user?.user_metadata?.interests as string[]) ?? [];
      if (Array.isArray(saved)) setInterests(saved);
      setResidence((data.user?.user_metadata?.residence as string) ?? null);
    });
  }, [sb]);

  const load = useCallback(async (ints: string[]) => {
    if (!premium) return;
    setBusy(true);
    try {
      const loc = resolveTiming(residence);
      const res = await fetch("/api/jyothishyam", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart, interests: ints, tz: loc.tz,
                               lat: loc.lat, lng: loc.lng }),
      });
      if (res.ok) setFc(await res.json());
    } catch { /* silent */ }
    finally { setBusy(false); }
  }, [chart, premium, residence]);

  useEffect(() => { if (premium) load(interests); /* eslint-disable-next-line */ }, [premium]);

  async function toggleInterest(it: string) {
    const next = interests.includes(it) ? interests.filter((x) => x !== it) : [...interests, it];
    setInterests(next);
    if (sb) sb.auth.updateUser({ data: { interests: next } });
    load(next);
  }

  if (signedIn === false) {
    return <div className="card p-6 text-center text-sm text-[var(--ink-soft)]">{t("chat_signin")}</div>;
  }
  if (!premium) {
    return (
      <div className="card space-y-3 p-6 text-center">
        <h3 className="heading-section text-lg">✦ {t("jyo_title")}</h3>
        <p className="text-sm text-[var(--ink-soft)]">{t("jyo_locked")}</p>
        <a href="/subscription" className="btn-gold inline-flex px-5">✦ {t("chat_upgrade")}</a>
      </div>
    );
  }

  const DayCard = ({ d, big }: { d: Day; big?: boolean }) => (
    <div className={`card p-4 ${big ? "" : "text-xs"}`}>
      <div className="flex items-baseline justify-between">
        <span className={`font-display font-semibold ${big ? "text-xl" : "text-sm"} text-[var(--gold)]`}>
          {d.weekday} · {d.date.slice(5)}
        </span>
        <span className="text-[10px] text-[var(--ink-faint)]">{d.vara_deity}</span>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
        <span className="text-[var(--ink-muted)]">Tithi</span>
        <span className="text-[var(--ink-soft)]">{d.tithi.name} ({d.tithi.group})</span>
        <span className="text-[var(--ink-muted)]">Nakshatra</span>
        <span className="text-[var(--ink-soft)]">{d.nakshatra.name} · {d.nakshatra.class}</span>
        <span className="text-[var(--ink-muted)]">Tarabala</span>
        <span className={d.tarabala.favourable ? "text-[var(--good)]" : "text-[var(--bad)]"}>{d.tarabala.name}</span>
        <span className="text-[var(--ink-muted)]">New ventures</span>
        <span className={VERDICT_COLOR[d.new_ventures]}>{t(`jyo_${d.new_ventures.replace(" ", "_")}`)}</span>
        <span className="text-[var(--ink-muted)]">Continuations</span>
        <span className={VERDICT_COLOR[d.continuations]}>{t(`jyo_${d.continuations.replace(" ", "_")}`)}</span>
      </div>
      {big && (
        <>
          <p className="mt-3 text-xs text-[var(--ink-soft)]">
            <b className="text-[var(--gold)]">{t("jyo_supports")}:</b> {d.nakshatra.supports}. {d.day_affairs}.
          </p>
          {d.focus.length > 0 && (
            <div className="mt-2 space-y-1">
              {d.focus.map((f) => (
                <p key={f.interest} className="text-xs text-[var(--ink-soft)]">
                  <b className="capitalize text-[var(--gold)]">{t(`int_${f.interest}`)}:</b> {f.note}
                </p>
              ))}
            </div>
          )}
        </>
      )}
      {d.cautions.length > 0 && (
        <ul className="mt-2 space-y-0.5">
          {d.cautions.map((c, i) => (
            <li key={i} className="text-[11px] text-[var(--warn)]">⚠ {c}</li>
          ))}
        </ul>
      )}
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex gap-1 rounded-lg border border-[var(--line)] p-0.5 text-xs">
          {(["today", "week"] as const).map((v) => (
            <button key={v} onClick={() => setView(v)}
                    className={`pill ${view === v ? "pill-active" : ""}`}>
              {t(`jyo_${v}`)}
            </button>
          ))}
        </div>
        {fc && <span className="text-[10px] text-[var(--ink-faint)]">✦ {t("chat_unlimited")}</span>}
      </div>

      {/* Interests */}
      <div>
        <p className="mb-1 text-xs text-[var(--ink-muted)]">{t("jyo_interests")}</p>
        <div className="flex flex-wrap gap-1.5">
          {INTERESTS.map((it) => (
            <button key={it} onClick={() => toggleInterest(it)}
                    className={`rounded-full border px-3 py-1 text-xs capitalize ${
                      interests.includes(it)
                        ? "border-[var(--gold)] bg-[var(--gold)]/15 text-[var(--gold)]"
                        : "border-[var(--line)] text-[var(--ink-soft)]"}`}>
              {t(`int_${it}`)}
            </button>
          ))}
        </div>
      </div>

      {busy && <p className="text-sm text-[var(--ink-muted)]">{t("computing")}</p>}

      {fc && view === "today" && <DayCard d={fc.today} big />}

      {fc && view === "week" && (
        <>
          <div className="card p-4 text-sm">
            <p><b className="text-[var(--gold)]">{t("jyo_week_deity")}:</b> {fc.period.week_deity}</p>
            <p className="mt-1 text-xs text-[var(--ink-soft)]">{fc.period.week_remedy}</p>
            <div className="mt-2 flex flex-wrap gap-3 text-xs">
              {fc.week_highlights.good_days.length > 0 && (
                <span className="text-[var(--good)]">✓ {t("jyo_best")}: {fc.week_highlights.good_days.map((d) => d.slice(5)).join(", ")}</span>
              )}
              {fc.week_highlights.careful_days.length > 0 && (
                <span className="text-[var(--bad)]">⚠ {t("jyo_careful")}: {fc.week_highlights.careful_days.map((d) => d.slice(5)).join(", ")}</span>
              )}
            </div>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {fc.week.map((d) => <DayCard key={d.date} d={d} />)}
          </div>
        </>
      )}

      <p className="text-center text-[10px] text-[var(--ink-faint)]">{fc?.note ?? t("jyo_computed_note")}</p>
    </div>
  );
}
