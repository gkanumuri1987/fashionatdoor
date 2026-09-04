"use client";

import { toDDMMYYYY } from "@/lib/date";

import { useCallback, useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

export interface BirthProfile {
  id: string;
  name: string;
  relation: string;
  birth_date: string;
  birth_time: string;
  time_accuracy: string;
  place_name: string;
  lat: number;
  lng: number;
  ayanamsa: string;
}

export interface HistoryEntry {
  id: string;
  person_name: string;
  birth_date: string;
  birth_time: string;
  time_accuracy: string;
  place_name: string;
  lat: number;
  lng: number;
  ayanamsa: string;
  lagna_sign: string | null;
  moon_nakshatra: string | null;
  created_at: string;
}

export interface ProfileDraft {
  name: string;
  birth_date: string;
  birth_time: string;
  time_accuracy: string;
  place_name: string;
  lat: number;
  lng: number;
  ayanamsa: string;
}

const FREE_LIMIT = 1;

/** "My Jaathakams": the SAVED jaathakam (1 free; more with subscription — the
 *  limit is ALSO enforced by a DB trigger, this UI mirrors it honestly) plus
 *  the account-level HISTORY of every chart computed while signed in. A
 *  jaathakam can be for ANY person — the name field says whose. */
export default function SavedProfiles({
  draft, onLoad,
}: {
  draft: ProfileDraft | null;
  onLoad: (p: BirthProfile) => void;
}) {
  const { t } = useLang();
  const sb = supabase();
  const [signedIn, setSignedIn] = useState(false);
  const [profiles, setProfiles] = useState<BirthProfile[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [premium, setPremium] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    if (!sb) return;
    const [{ data: p }, { data: h }, flagsRes] = await Promise.all([
      sb.from("birth_profiles")
        .select("id,name,relation,birth_date,birth_time,time_accuracy,place_name,lat,lng,ayanamsa")
        .order("created_at", { ascending: false }).limit(50),
      sb.from("chart_history")
        .select("id,person_name,birth_date,birth_time,time_accuracy,place_name,lat,lng,ayanamsa,lagna_sign,moon_nakshatra,created_at")
        .order("created_at", { ascending: false }).limit(10)
        .then((r) => r, () => ({ data: null })),
      sb.from("user_flags").select("is_premium").maybeSingle()
        .then((r) => r, () => ({ data: null })),
    ]);
    if (p) setProfiles(p as BirthProfile[]);
    if (h) setHistory(h as HistoryEntry[]);
    setPremium(Boolean((flagsRes.data as { is_premium?: boolean } | null)?.is_premium));
  }, [sb]);

  useEffect(() => {
    if (!sb) return;
    sb.auth.getUser().then(({ data }) => {
      const yes = Boolean(data.user);
      setSignedIn(yes);
      if (yes) refresh();
    });
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      const yes = Boolean(session?.user);
      setSignedIn(yes);
      if (yes) refresh(); else { setProfiles([]); setHistory([]); }
    });
    return () => sub.subscription.unsubscribe();
  }, [sb, refresh]);

  if (!sb || !signedIn) return null;

  const atLimit = !premium && profiles.length >= FREE_LIMIT;

  async function save() {
    if (!sb || !draft) return;
    setBusy(true); setMsg("");
    const { data: u } = await sb.auth.getUser();
    if (!u.user) { setBusy(false); return; }
    const { error } = await sb.from("birth_profiles").insert({
      user_id: u.user.id,
      name: saveName.trim() || draft.name || "Unnamed",
      birth_date: draft.birth_date,
      birth_time: draft.birth_time,
      time_accuracy: draft.time_accuracy,
      place_name: draft.place_name,
      lat: draft.lat,
      lng: draft.lng,
      ayanamsa: draft.ayanamsa,
    });
    setBusy(false);
    if (error) {
      if (error.message.includes("FREE_LIMIT_REACHED")) {
        setMsg(t("limit_reached"));
      } else if (error.code === "42P01") {
        setMsg("Profiles table missing — run db_migrations in Supabase.");
      } else {
        setMsg(error.message);
      }
      return;
    }
    setSaveName(""); setMsg(t("saved_ok"));
    refresh();
  }

  async function remove(id: string) {
    if (!sb) return;
    await sb.from("birth_profiles").delete().eq("id", id);
    refresh();
  }

  function loadHistory(h: HistoryEntry) {
    onLoad({
      id: h.id, name: h.person_name, relation: "history",
      birth_date: h.birth_date, birth_time: h.birth_time,
      time_accuracy: h.time_accuracy, place_name: h.place_name,
      lat: h.lat, lng: h.lng, ayanamsa: h.ayanamsa,
    });
  }

  return (
    <div className="card mt-4 p-4">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-sm font-semibold text-[var(--ink-soft)]">{t("saved_profiles")}</p>
        <span className="text-[10px] text-[var(--ink-faint)]">
          {premium ? "✦ premium" : `${profiles.length}/${FREE_LIMIT} ${t("free_slot")}`}
        </span>
      </div>

      {draft && !atLimit && (
        <div className="mb-3 flex gap-2">
          <input
            value={saveName} placeholder={t("name_ph")}
            onChange={(e) => setSaveName(e.target.value)}
            className="input flex-1 text-sm"
          />
          <button onClick={save} disabled={busy} className="btn-gold px-3 py-1.5 text-sm">
            {t("save_current")}
          </button>
        </div>
      )}
      {draft && atLimit && (
        <a href="/subscription"
           className="mb-3 block rounded-lg border border-[var(--line-gold)] bg-[var(--gold)]/10 px-3 py-2 text-xs text-[var(--gold)] hover:bg-[var(--gold)]/15">
          ✦ {t("limit_reached")} →
        </a>
      )}
      {msg && <p className="mb-2 text-xs text-[var(--ink-muted)]">{msg}</p>}

      {profiles.length === 0 ? (
        <p className="text-xs text-[var(--ink-muted)]">{t("no_profiles")}</p>
      ) : (
        <ul className="divide-y divide-[var(--line-soft)]">
          {profiles.map((p) => (
            <li key={p.id} className="flex items-center justify-between py-1.5 text-sm">
              <button onClick={() => onLoad(p)} className="text-left hover:text-[var(--gold)]">
                <span className="font-medium">{p.name}</span>{" "}
                <span className="text-[var(--ink-muted)]">
                  {toDDMMYYYY(p.birth_date)} {p.birth_time.slice(0, 5)} · {p.place_name.split(",")[0]}
                </span>
              </button>
              <button
                onClick={() => remove(p.id)}
                className="ml-3 text-xs text-[var(--ink-faint)] hover:text-red-500"
                aria-label={`Delete ${p.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {history.length > 0 && (
        <>
          <p className="mb-1 mt-4 text-xs font-semibold text-[var(--ink-muted)]">
            {t("recent_charts")}
          </p>
          <ul className="divide-y divide-[var(--line-soft)]">
            {history.map((h) => (
              <li key={h.id} className="py-1.5 text-xs">
                <button onClick={() => loadHistory(h)}
                        className="w-full text-left hover:text-[var(--gold)]">
                  <span className="text-[var(--ink-soft)]">
                    {h.person_name || "—"} · {toDDMMYYYY(h.birth_date)} {h.birth_time.slice(0, 5)}
                    {" · "}{h.place_name.split(",")[0]}
                  </span>
                  {h.lagna_sign && (
                    <span className="ml-2 text-[var(--ink-faint)]">
                      {h.lagna_sign} lagna{h.moon_nakshatra ? ` · ${h.moon_nakshatra}` : ""}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
