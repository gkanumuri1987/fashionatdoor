"use client";

/** Login popup — today's Jyothishyam for the member's most-recent saved
 *  jaathakam. Shows once per day (localStorage), Plus/Lifetime Plus only. */

import { useEffect, useState } from "react";
import { chatUnlimited, useAccount } from "@/lib/account";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";
import { resolveTiming } from "@/lib/locations";

export default function TodayPopup() {
  const { t } = useLang();
  const sb = supabase();
  const { account, signedIn } = useAccount();
  const [today, setToday] = useState<null | {
    weekday: string; vara_deity: string;
    tithi: { name: string; group: string };
    nakshatra: { name: string; class: string };
    tarabala: { name: string; favourable: boolean };
    new_ventures: string; cautions: string[];
  }>(null);
  const [open, setOpen] = useState(false);

  const premium = chatUnlimited(account);

  useEffect(() => {
    if (!sb || !signedIn || !premium) return;
    const key = `jyo_seen_${new Date().toISOString().slice(0, 10)}`;
    try { if (localStorage.getItem(key)) return; } catch { /* ignore */ }

    (async () => {
      const { data: profs } = await sb.from("birth_profiles")
        .select("birth_date,birth_time,lat,lng,ayanamsa,name")
        .order("created_at", { ascending: false }).limit(1);
      const p = profs?.[0];
      if (!p) return;
      const chartRes = await fetch("/api/chart", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date: p.birth_date, time: p.birth_time.slice(0, 5),
                               lat: p.lat, lng: p.lng, ayanamsa: p.ayanamsa }),
      });
      if (!chartRes.ok) return;
      const chart = await chartRes.json();
      const { data: u } = await sb.auth.getUser();
      const interests = (u.user?.user_metadata?.interests as string[]) ?? [];
      const loc = resolveTiming((u.user?.user_metadata?.residence as string) ?? null);
      const fRes = await fetch("/api/jyothishyam", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart, interests, tz: loc.tz, lat: loc.lat, lng: loc.lng }),
      });
      if (!fRes.ok) return;
      const f = await fRes.json();
      setToday(f.today);
      setOpen(true);
      try { localStorage.setItem(key, "1"); } catch { /* ignore */ }
    })().catch(() => {});
  }, [sb, signedIn, premium]);

  if (!open || !today) return null;

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4"
         onClick={() => setOpen(false)}>
      <div className="absolute inset-0 bg-black/65 backdrop-blur-sm" />
      <div className="card relative w-full max-w-sm p-6" onClick={(e) => e.stopPropagation()}>
        <button onClick={() => setOpen(false)} aria-label="Close"
                className="absolute right-4 top-3 text-[var(--ink-muted)] hover:text-[var(--ink)]">✕</button>
        <h3 className="heading-display text-2xl">✦ {t("jyo_popup_title")}</h3>
        <p className="mt-1 text-xs text-[var(--gold)]">{today.weekday} · {today.vara_deity}</p>
        <div className="mt-4 grid grid-cols-2 gap-x-3 gap-y-1.5 text-sm">
          <span className="text-[var(--ink-muted)]">Tithi</span>
          <span className="text-[var(--ink-soft)]">{today.tithi.name} ({today.tithi.group})</span>
          <span className="text-[var(--ink-muted)]">Nakshatra</span>
          <span className="text-[var(--ink-soft)]">{today.nakshatra.name} · {today.nakshatra.class}</span>
          <span className="text-[var(--ink-muted)]">Tarabala</span>
          <span className={today.tarabala.favourable ? "text-[var(--good)]" : "text-[var(--bad)]"}>
            {today.tarabala.name}
          </span>
          <span className="text-[var(--ink-muted)]">New ventures</span>
          <span className={today.new_ventures === "favourable" ? "text-[var(--good)]"
                           : today.new_ventures === "avoid" ? "text-[var(--bad)]" : "text-[var(--warn)]"}>
            {t(`jyo_${today.new_ventures}`)}
          </span>
        </div>
        {today.cautions.length > 0 && (
          <ul className="mt-3 space-y-0.5">
            {today.cautions.slice(0, 2).map((c, i) => (
              <li key={i} className="text-xs text-[var(--warn)]">⚠ {c}</li>
            ))}
          </ul>
        )}
        <a href="/kundli" onClick={() => setOpen(false)}
           className="btn-gold mt-5 block w-full py-2 text-center text-sm">
          {t("jyo_popup_view")}
        </a>
      </div>
    </div>
  );
}
