"use client";

/** Reset password — the page the emailed reset link lands on. Supabase puts
 *  the user into a temporary recovery session; we set the new password (with
 *  confirm) via updateUser, then send them to sign in. */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";
import { JaathakaMark } from "@/components/Logo";

export default function ResetPasswordPage() {
  const { t } = useLang();
  const sb = supabase();
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [good, setGood] = useState(false);

  useEffect(() => {
    if (!sb) return;
    // The recovery link creates a session automatically; confirm it's present.
    sb.auth.getSession().then(({ data }) => setReady(Boolean(data.session)));
    const { data: sub } = sb.auth.onAuthStateChange((event, session) => {
      if (event === "PASSWORD_RECOVERY" || session) setReady(true);
    });
    return () => sub.subscription.unsubscribe();
  }, [sb]);

  async function save() {
    if (!sb) return;
    if (password.length < 6) { setGood(false); setMsg(t("auth_password_short")); return; }
    if (password !== confirm) { setGood(false); setMsg(t("auth_mismatch")); return; }
    setBusy(true); setMsg("");
    const { error } = await sb.auth.updateUser({ password });
    setBusy(false);
    if (error) { setGood(false); setMsg(error.message); return; }
    setGood(true); setMsg(t("auth_reset_done"));
    setTimeout(() => router.push("/kundli"), 1500);
  }

  return (
    <main className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center px-4 py-12">
      <header className="text-center">
        <h1 className="heading-display text-4xl">{t("auth_reset_title")}</h1>
        <div className="ornament mt-3 text-xs">✦</div>
      </header>

      <div className="card mt-8 p-7">
        {!ready ? (
          <p className="text-center text-sm text-[var(--ink-muted)]">{t("auth_reset_open_link")}</p>
        ) : (
          <>
            <label className="block text-sm">
              <span className="text-xs text-[var(--ink-muted)]">{t("auth_new_password")}</span>
              <input type="password" value={password} placeholder={t("auth_password_ph")}
                     onChange={(e) => setPassword(e.target.value)}
                     className="input mt-1.5 py-3 text-base" autoComplete="new-password" />
            </label>
            <label className="mt-4 block text-sm">
              <span className="text-xs text-[var(--ink-muted)]">{t("auth_confirm_ph")}</span>
              <input type="password" value={confirm} placeholder={t("auth_confirm_ph")}
                     onChange={(e) => setConfirm(e.target.value)}
                     className="input mt-1.5 py-3 text-base" autoComplete="new-password"
                     onKeyDown={(e) => e.key === "Enter" && save()} />
            </label>
            <button onClick={save} disabled={busy} className="btn-gold mt-6 w-full py-3 text-base">
              {busy ? "…" : t("auth_set_password")}
            </button>
          </>
        )}
        {msg && (
          <p className={`mt-4 rounded-lg border px-3 py-2.5 text-center text-sm ${
            good ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
                 : "border-orange-500/40 bg-orange-500/10 text-orange-200"}`}>
            {msg}
          </p>
        )}
      </div>
    </main>
  );
}
