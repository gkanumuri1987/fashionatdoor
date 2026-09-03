"use client";

/** Sign in / create account — a full, properly designed page (the old modal
 *  was cramped by the sidebar's layout context). Password is the primary
 *  path (no email quota); the email-code tab remains for passwordless. */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

function friendly(msg: string, t: (k: string) => string): string {
  if (/rate limit/i.test(msg)) return t("auth_rate_limited");
  if (/invalid login credentials/i.test(msg)) return t("auth_bad_credentials");
  if (/already registered/i.test(msg)) return t("auth_exists");
  return msg;
}

export default function SignInPage() {
  const { t } = useLang();
  const sb = supabase();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"password" | "otp">("password");
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [good, setGood] = useState(false);

  useEffect(() => {
    if (!sb) return;
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      if (session?.user) router.push("/kundli");
    });
    sb.auth.getUser().then(({ data }) => { if (data.user) router.push("/profile"); });
    return () => sub.subscription.unsubscribe();
  }, [sb, router]);

  async function passwordAuth() {
    if (!sb || !email.trim() || password.length < 6) {
      setGood(false); setMsg(t("auth_password_short")); return;
    }
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithPassword({ email: email.trim(), password });
    if (!error) { setBusy(false); return; }
    if (/invalid login credentials/i.test(error.message)) {
      const { data, error: e2 } = await sb.auth.signUp({ email: email.trim(), password });
      setBusy(false);
      if (e2) { setGood(false); setMsg(friendly(e2.message, t)); return; }
      if (data.user && !data.session) { setGood(true); setMsg(t("auth_confirm_sent")); }
      else if (data.user?.identities?.length === 0) { setGood(false); setMsg(t("auth_bad_credentials")); }
      return;
    }
    setBusy(false); setGood(false); setMsg(friendly(error.message, t));
  }

  async function sendOtp() {
    if (!sb || !email.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithOtp({
      email: email.trim(), options: { shouldCreateUser: true },
    });
    setBusy(false);
    if (error) { setGood(false); setMsg(friendly(error.message, t)); return; }
    setOtpSent(true); setGood(true); setMsg(t("code_sent"));
  }

  async function verifyOtp() {
    if (!sb || !otp.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await sb.auth.verifyOtp({
      email: email.trim(), token: otp.trim(), type: "email",
    });
    setBusy(false);
    if (error) { setGood(false); setMsg(friendly(error.message, t)); }
  }

  return (
    <main className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center px-4 py-12">
      <header className="text-center">
        <h1 className="heading-display text-4xl">{t("app_title")}</h1>
        <div className="ornament mt-3 text-xs">✦</div>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">{t("gate_body")}</p>
      </header>

      <div className="card mt-8 p-7">
        <div className="flex gap-1 rounded-xl border border-[var(--line)] p-1 text-sm">
          {(["password", "otp"] as const).map((m) => (
            <button key={m} onClick={() => { setMode(m); setMsg(""); }}
                    className={`flex-1 rounded-lg px-3 py-2 transition-colors ${
                      mode === m ? "pill-active" : "text-[var(--ink-soft)] hover:text-[var(--ink)]"}`}>
              {m === "password" ? `🔑 ${t("auth_tab_password")}` : `✉️ ${t("auth_tab_code")}`}
            </button>
          ))}
        </div>

        <label className="mt-5 block text-sm">
          <span className="text-xs text-[var(--ink-muted)]">Email</span>
          <input type="email" value={email} placeholder="you@example.com"
                 onChange={(e) => setEmail(e.target.value)}
                 className="input mt-1.5 py-3 text-base" autoComplete="email" />
        </label>

        {mode === "password" ? (
          <>
            <label className="mt-4 block text-sm">
              <span className="text-xs text-[var(--ink-muted)]">{t("auth_tab_password")}</span>
              <input type="password" value={password} placeholder={t("auth_password_ph")}
                     onChange={(e) => setPassword(e.target.value)}
                     className="input mt-1.5 py-3 text-base" autoComplete="current-password"
                     onKeyDown={(e) => e.key === "Enter" && passwordAuth()} />
            </label>
            <button onClick={passwordAuth} disabled={busy}
                    className="btn-gold mt-6 w-full py-3 text-base">
              {busy ? "…" : t("auth_continue")}
            </button>
            <p className="mt-3 text-center text-xs text-[var(--ink-faint)]">
              {t("auth_password_hint")}
            </p>
          </>
        ) : (
          <>
            {otpSent && (
              <label className="mt-4 block text-sm">
                <span className="text-xs text-[var(--ink-muted)]">{t("code_ph")}</span>
                <input value={otp} placeholder="123456"
                       onChange={(e) => setOtp(e.target.value)}
                       className="input mt-1.5 py-3 text-center text-xl tracking-[0.4em]"
                       inputMode="numeric" maxLength={6}
                       onKeyDown={(e) => e.key === "Enter" && verifyOtp()} />
              </label>
            )}
            <button onClick={otpSent ? verifyOtp : sendOtp} disabled={busy}
                    className="btn-gold mt-6 w-full py-3 text-base">
              {busy ? "…" : otpSent ? t("verify_code") : t("send_code")}
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

      <p className="mt-6 text-center text-xs text-[var(--ink-muted)]">{t("disclaimer")}</p>
    </main>
  );
}
