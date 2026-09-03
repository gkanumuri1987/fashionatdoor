"use client";

/** Sign in · Sign up · Forgot password — three explicit modes.
 *  Sign up takes a confirm-password. Forgot password emails a reset link that
 *  lands on /reset-password. Email-code (OTP) stays as a passwordless option. */

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

type Mode = "signin" | "signup" | "forgot" | "otp";

function friendly(msg: string, t: (k: string) => string): string {
  if (/rate limit/i.test(msg)) return t("auth_rate_limited");
  if (/invalid login credentials/i.test(msg)) return t("auth_bad_credentials");
  if (/already registered|already exists/i.test(msg)) return t("auth_exists");
  if (/should be at least|password/i.test(msg) && /6/.test(msg)) return t("auth_password_short");
  return msg;
}

export default function SignInPage() {
  const { t } = useLang();
  const sb = supabase();
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
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

  function setError(m: string) { setGood(false); setMsg(m); }
  function setOk(m: string) { setGood(true); setMsg(m); }

  async function signIn() {
    if (!sb) return;
    if (!email.trim() || password.length < 6) { setError(t("auth_password_short")); return; }
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithPassword({ email: email.trim(), password });
    setBusy(false);
    if (error) setError(friendly(error.message, t));  // success → redirect via listener
  }

  async function signUp() {
    if (!sb) return;
    if (!email.trim() || password.length < 6) { setError(t("auth_password_short")); return; }
    if (password !== confirm) { setError(t("auth_mismatch")); return; }
    setBusy(true); setMsg("");
    const { data, error } = await sb.auth.signUp({ email: email.trim(), password });
    setBusy(false);
    if (error) { setError(friendly(error.message, t)); return; }
    if (data.session) return;                          // autoconfirm on → logged in
    if (data.user && data.user.identities?.length === 0) { setError(t("auth_exists")); return; }
    setOk(t("auth_confirm_sent"));                     // confirmation email sent
  }

  async function forgot() {
    if (!sb || !email.trim()) { setError(t("auth_need_email")); return; }
    setBusy(true); setMsg("");
    const { error } = await sb.auth.resetPasswordForEmail(email.trim(), {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    setBusy(false);
    if (error) { setError(friendly(error.message, t)); return; }
    setOk(t("auth_reset_sent"));
  }

  async function sendOtp() {
    if (!sb || !email.trim()) { setError(t("auth_need_email")); return; }
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithOtp({
      email: email.trim(), options: { shouldCreateUser: true },
    });
    setBusy(false);
    if (error) { setError(friendly(error.message, t)); return; }
    setOtpSent(true); setOk(t("code_sent"));
  }

  async function verifyOtp() {
    if (!sb || !otp.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await sb.auth.verifyOtp({ email: email.trim(), token: otp.trim(), type: "email" });
    setBusy(false);
    if (error) setError(friendly(error.message, t));
  }

  const TABS: [Mode, string][] = [
    ["signin", t("auth_tab_signin")],
    ["signup", t("auth_tab_signup")],
    ["otp", t("auth_tab_code")],
  ];

  return (
    <main className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center px-4 py-12">
      <header className="text-center">
        <h1 className="heading-display text-4xl">{t("app_title")}</h1>
        <div className="ornament mt-3 text-xs">✦</div>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">
          {mode === "signup" ? t("about_join_body") : t("gate_body")}
        </p>
      </header>

      <div className="card mt-8 p-7">
        {mode !== "forgot" && (
          <div className="flex gap-1 rounded-xl border border-[var(--line)] p-1 text-sm">
            {TABS.map(([m, label]) => (
              <button key={m} onClick={() => { setMode(m); setMsg(""); }}
                      className={`flex-1 rounded-lg px-3 py-2 transition-colors ${
                        mode === m ? "pill-active" : "text-[var(--ink-soft)] hover:text-[var(--ink)]"}`}>
                {label}
              </button>
            ))}
          </div>
        )}

        {mode === "forgot" && (
          <h3 className="heading-section text-lg">{t("auth_forgot_title")}</h3>
        )}

        <label className="mt-5 block text-sm">
          <span className="text-xs text-[var(--ink-muted)]">Email</span>
          <input type="email" value={email} placeholder="you@example.com"
                 onChange={(e) => setEmail(e.target.value)}
                 className="input mt-1.5 py-3 text-base" autoComplete="email" />
        </label>

        {(mode === "signin" || mode === "signup") && (
          <label className="mt-4 block text-sm">
            <span className="text-xs text-[var(--ink-muted)]">{t("auth_tab_password")}</span>
            <input type="password" value={password} placeholder={t("auth_password_ph")}
                   onChange={(e) => setPassword(e.target.value)}
                   className="input mt-1.5 py-3 text-base"
                   autoComplete={mode === "signup" ? "new-password" : "current-password"}
                   onKeyDown={(e) => e.key === "Enter" && (mode === "signin" ? signIn() : signUp())} />
          </label>
        )}

        {mode === "signup" && (
          <label className="mt-4 block text-sm">
            <span className="text-xs text-[var(--ink-muted)]">{t("auth_confirm_ph")}</span>
            <input type="password" value={confirm} placeholder={t("auth_confirm_ph")}
                   onChange={(e) => setConfirm(e.target.value)}
                   className="input mt-1.5 py-3 text-base" autoComplete="new-password"
                   onKeyDown={(e) => e.key === "Enter" && signUp()} />
          </label>
        )}

        {mode === "otp" && otpSent && (
          <label className="mt-4 block text-sm">
            <span className="text-xs text-[var(--ink-muted)]">{t("code_ph")}</span>
            <input value={otp} placeholder="123456"
                   onChange={(e) => setOtp(e.target.value)}
                   className="input mt-1.5 py-3 text-center text-xl tracking-[0.4em]"
                   inputMode="numeric" maxLength={6}
                   onKeyDown={(e) => e.key === "Enter" && verifyOtp()} />
          </label>
        )}

        <button
          onClick={() => (mode === "signin" ? signIn() : mode === "signup" ? signUp()
                          : mode === "forgot" ? forgot() : otpSent ? verifyOtp() : sendOtp())}
          disabled={busy} className="btn-gold mt-6 w-full py-3 text-base">
          {busy ? "…"
            : mode === "signin" ? t("sign_in")
            : mode === "signup" ? t("about_join_btn")
            : mode === "forgot" ? t("auth_send_reset")
            : otpSent ? t("verify_code") : t("send_code")}
        </button>

        {mode === "signin" && (
          <button onClick={() => { setMode("forgot"); setMsg(""); }}
                  className="mt-3 w-full text-center text-xs text-[var(--gold)] underline">
            {t("auth_forgot_link")}
          </button>
        )}
        {mode === "forgot" && (
          <button onClick={() => { setMode("signin"); setMsg(""); }}
                  className="mt-3 w-full text-center text-xs text-[var(--ink-muted)] underline">
            ← {t("auth_back_signin")}
          </button>
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
