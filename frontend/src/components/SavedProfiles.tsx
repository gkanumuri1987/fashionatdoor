"use client";

import { useCallback, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { useLang } from "@/lib/i18n";

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

/** Saved birth profiles (Supabase, RLS-scoped to the signed-in user).
 *  `draft` is the currently computed birth data, offered for saving;
 *  `onLoad` pushes a saved profile back into the form. Hidden unless signed in. */
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
  const [saveName, setSaveName] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const refresh = useCallback(async () => {
    if (!sb) return;
    const { data, error } = await sb
      .from("birth_profiles")
      .select("id,name,relation,birth_date,birth_time,time_accuracy,place_name,lat,lng,ayanamsa")
      .order("created_at", { ascending: false })
      .limit(50);
    if (!error && data) setProfiles(data as BirthProfile[]);
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
      if (yes) refresh(); else setProfiles([]);
    });
    return () => sub.subscription.unsubscribe();
  }, [sb, refresh]);

  if (!sb || !signedIn) return null;

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
      // 42P01 = table missing — migration not yet applied.
      setMsg(error.code === "42P01"
        ? "Profiles table missing — run db_migrations/001_birth_profiles.sql in Supabase."
        : error.message);
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

  return (
    <div className="mt-4 rounded-lg border border-[var(--line)] bg-[var(--surface-solid)] p-4">
      <p className="mb-2 text-sm font-semibold text-[var(--ink-soft)]">{t("saved_profiles")}</p>
      {draft && (
        <div className="mb-3 flex gap-2">
          <input
            value={saveName} placeholder={t("name_ph")}
            onChange={(e) => setSaveName(e.target.value)}
            className="flex-1 rounded-md border border-[var(--line)] bg-[var(--surface-deep)] px-3 py-1.5 text-sm text-[var(--ink)]"
          />
          <button
            onClick={save} disabled={busy}
            className="rounded-md bg-[var(--gold)] px-3 py-1.5 text-sm text-[var(--on-gold)] font-semibold hover:bg-[var(--gold-bright)] disabled:opacity-50"
          >{t("save_current")}</button>
        </div>
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
                  {p.birth_date} {p.birth_time.slice(0, 5)} · {p.place_name}
                </span>
              </button>
              <button
                onClick={() => remove(p.id)}
                className="ml-3 text-xs text-[var(--ink-faint)] hover:text-red-600"
                aria-label={`Delete ${p.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
