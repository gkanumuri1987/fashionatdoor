"use client";

/** Profile — everything associated with the account in one place:
 *  display name (editable), email, plan & credits, referral link, the
 *  family's saved jaathakams (add via /kundli, subject to the free limit),
 *  recent chart history, and sign out. */

import Link from "next/link";
import { useEffect, useState } from "react";
import AuthBar from "@/components/AuthBar";
import SavedProfiles from "@/components/SavedProfiles";
import { useAccount } from "@/lib/account";
import { copyText } from "@/lib/clipboard";
import { LOCATIONS } from "@/lib/locations";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

export default function ProfilePage() {
  const { t } = useLang();
  const sb = supabase();
  const { account, signedIn, refresh } = useAccount();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [residence, setResidence] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [refCopied, setRefCopied] = useState(false);

  useEffect(() => {
    if (!sb) return;
    sb.auth.getUser().then(({ data }) => {
      if (data.user) {
        setEmail(data.user.email ?? "");
        setFullName((data.user.user_metadata?.full_name as string) ?? "");
        setResidence((data.user.user_metadata?.residence as string) ?? "");
      }
    });
  }, [sb, signedIn]);

  async function saveName() {
    if (!sb) return;
    setSaving(true); setMsg("");
    const { error } = await sb.auth.updateUser({
      data: { full_name: fullName.trim(), residence },
    });
    setSaving(false);
    setMsg(error ? error.message : t("saved_ok"));
  }

  async function logout() {
    if (!sb) return;
    await sb.auth.signOut();
    refresh();
  }

  if (signedIn === false) {
    return (
      <main className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="heading-display text-3xl">{t("nav_profile")}</h1>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">{t("chat_signin")}</p>
        <div className="mt-5 flex justify-center"><AuthBar /></div>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-10">
      <header className="mb-6 text-center">
        <h1 className="heading-display text-4xl">{t("nav_profile")}</h1>
        <div className="ornament mt-2 text-xs">✦</div>
      </header>

      {/* Identity */}
      <section className="card p-5">
        <h3 className="heading-section text-lg">{t("prof_identity")}</h3>
        <div className="mt-3 space-y-3 text-sm">
          <label className="block">
            <span className="text-xs text-[var(--ink-muted)]">{t("prof_name")}</span>
            <div className="mt-1 flex gap-2">
              <input value={fullName} onChange={(e) => setFullName(e.target.value)}
                     placeholder={t("name_ph")} className="input flex-1" />
              <button onClick={saveName} disabled={saving} className="btn-gold px-4 text-sm">
                {saving ? "…" : t("prof_save")}
              </button>
            </div>
          </label>
          <label className="block">
            <span className="text-xs text-[var(--ink-muted)]">{t("prof_residence")}</span>
            <select value={residence} onChange={(e) => setResidence(e.target.value)}
                    className="input mt-1">
              <option value="">{t("prof_residence_auto")}</option>
              {LOCATIONS.map((l) => <option key={l.key} value={l.key}>{l.label}</option>)}
            </select>
            <span className="mt-1 block text-[10px] text-[var(--ink-faint)]">{t("prof_residence_hint")}</span>
          </label>
          <div>
            <span className="text-xs text-[var(--ink-muted)]">Email</span>
            <div className="mt-1 text-[var(--ink-soft)]">{email}</div>
          </div>
          {msg && <p className="text-xs text-[var(--gold)]">{msg}</p>}
        </div>
      </section>

      {/* Plan & credits & referral */}
      {account && (
        <section className="card mt-4 p-5">
          <div className="flex items-center justify-between">
            <h3 className="heading-section text-lg">{t("acct_title")}</h3>
            <Link href="/subscription" className="text-xs text-[var(--gold)] underline">
              {t("nav_subscription")} →
            </Link>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg border border-[var(--line-soft)] p-3">
              <div className="text-xs text-[var(--ink-muted)]">{t("acct_plan")}</div>
              <div className="mt-0.5 text-[var(--gold)]">
                {account.plan && account.plan !== "free"
                  ? t(`plan_${account.plan}`)
                  : account.is_premium ? t("plan_premium") : t("plan_free")}
              </div>
            </div>
            <div className="rounded-lg border border-[var(--line-soft)] p-3">
              <div className="text-xs text-[var(--ink-muted)]">{t("acct_credits")}</div>
              <div className="mt-0.5 text-[var(--gold)]">◈ {account.credits}</div>
            </div>
          </div>
          {account.referral_code && (
            <div className="mt-3 text-xs">
              <p className="text-[var(--ink-muted)]">{t("acct_ref")}</p>
              <div className="mt-1.5 flex gap-2">
                <code className="input flex-1 truncate py-1.5 text-[var(--gold)]">
                  {`${typeof window !== "undefined" ? window.location.origin : ""}/?ref=${account.referral_code}`}
                </code>
                <button onClick={async () => setRefCopied(await copyText(`${window.location.origin}/?ref=${account.referral_code}`))}
                        className="btn-gold px-3 py-1 text-xs">
                  {refCopied ? t("copied") : t("copy")}
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {/* Family jaathakams + history (SavedProfiles in list mode) */}
      <section className="mt-4">
        <div className="mb-1 flex items-center justify-between px-1">
          <h3 className="heading-section text-lg">{t("prof_family")}</h3>
          <Link href="/kundli" className="text-xs text-[var(--gold)] underline">
            {t("prof_add_member")} →
          </Link>
        </div>
        <SavedProfiles draft={null}
                       onLoad={() => { window.location.href = "/kundli"; }} />
      </section>

      {/* Sign out */}
      <div className="mt-6 text-center">
        <button onClick={logout} className="btn-ghost px-6 text-sm">
          {t("sign_out")}
        </button>
      </div>
    </main>
  );
}
