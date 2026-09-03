"use client";

/** Sign-in state + auth modal. The modal is a centered fixed overlay (the old
 *  dropdown opened downward and was clipped at the bottom of the sidebar).
 *  Two ways in: PASSWORD (no email needed after signup — immune to email
 *  rate limits) and email CODE (passwordless OTP). */

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

function friendly(msg: string, t: (k: string) => string): string {
  if (/rate limit/i.test(msg)) return t("auth_rate_limited");
  if (/invalid login credentials/i.test(msg)) return t("auth_bad_credentials");
  if (/already registered/i.test(msg)) return t("auth_exists");
  return msg;
}

export default function AuthBar() {
  const { t } = useLang();
  const sb = supabase();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [mode, setMode] = useState<"password" | "otp">("password");
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!sb) return;
    sb.auth.getUser().then(({ data }) => setUserEmail(data.user?.email ?? null));
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      setUserEmail(session?.user?.email ?? null);
      if (session?.user) setOpen(false);
    });
    return () => sub.subscription.unsubscribe();
  }, [sb]);

  if (!sb) return null;

  async function passwordAuth() {
    if (!sb || !email.trim() || password.length < 6) {
      setMsg(t("auth_password_short"));
      return;
    }
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithPassword({
      email: email.trim(), password,
    });
    if (!error) { setBusy(false); return; }  // onAuthStateChange closes modal
    if (/invalid login credentials/i.test(error.message)) {
      // No such account (or wrong password) → offer to create.
      const { data, error: e2 } = await sb.auth.signUp({
        email: email.trim(), password,
      });
      setBusy(false);
      if (e2) { setMsg(friendly(e2.message, t)); return; }
      if (data.user && !data.session) {
        setMsg(t("auth_confirm_sent"));       // email confirmation pending
      } else if (data.user?.identities?.length === 0) {
        setMsg(t("auth_bad_credentials"));    // account exists, wrong password
      }
      return;
    }
    setBusy(false);
    setMsg(friendly(error.message, t));
  }

  async function sendOtp() {
    if (!sb || !email.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithOtp({
      email: email.trim(), options: { shouldCreateUser: true },
    });
    setBusy(false);
    if (error) { setMsg(friendly(error.message, t)); return; }
    setOtpSent(true);
    setMsg(t("code_sent"));
  }

  async function verifyOtp() {
    if (!sb || !otp.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await sb.auth.verifyOtp({
      email: email.trim(), token: otp.trim(), type: "email",
    });
    setBusy(false);
    if (error) { setMsg(friendly(error.message, t)); return; }
    setOtpSent(false); setOtp("");
  }

  if (userEmail) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <a href="/profile" className="truncate text-xs text-[var(--ink-muted)] hover:text-[var(--gold)]"
           title={t("nav_profile")}>
          {userEmail}
        </a>
        <button onClick={() => sb.auth.signOut()} className="btn-ghost px-3 py-1 text-xs">
          {t("sign_out")}
        </button>
      </div>
    );
  }

  return (
    <>
      <button onClick={() => setOpen(true)} className="btn-gold w-full py-1.5 text-sm">
        {t("sign_in")}
      </button>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
             onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-black/65 backdrop-blur-sm" />
          <div className="card relative w-full max-w-sm p-6"
               onClick={(e) => e.stopPropagation()}>
            <button onClick={() => setOpen(false)} aria-label="Close"
                    className="absolute right-4 top-3 text-[var(--ink-muted)] hover:text-[var(--ink)]">✕</button>
            <h3 className="heading-section text-lg">{t("sign_in_email")}</h3>

            <div className="mt-3 flex gap-1 rounded-lg border border-[var(--line)] p-0.5 text-xs">
              {(["password", "otp"] as const).map((m) => (
                <button key={m} onClick={() => { setMode(m); setMsg(""); }}
                        className={`flex-1 rounded-md px-2 py-1.5 ${mode === m ? "pill-active" : "text-[var(--ink-soft)]"}`}>
                  {m === "password" ? t("auth_tab_password") : t("auth_tab_code")}
                </button>
              ))}
            </div>

            <input type="email" value={email} placeholder="you@example.com"
                   onChange={(e) => setEmail(e.target.value)}
                   className="input mt-3" autoComplete="email" />

            {mode === "password" ? (
              <>
                <input type="password" value={password} placeholder={t("auth_password_ph")}
                       onChange={(e) => setPassword(e.target.value)}
                       className="input mt-2" autoComplete="current-password"
                       onKeyDown={(e) => e.key === "Enter" && passwordAuth()} />
                <button onClick={passwordAuth} disabled={busy}
                        className="btn-gold mt-3 w-full">
                  {busy ? "…" : t("auth_continue")}
                </button>
                <p className="mt-2 text-center text-[10px] text-[var(--ink-faint)]">
                  {t("auth_password_hint")}
                </p>
              </>
            ) : (
              <>
                {otpSent && (
                  <input value={otp} placeholder={t("code_ph")}
                         onChange={(e) => setOtp(e.target.value)}
                         className="input mt-2" inputMode="numeric"
                         onKeyDown={(e) => e.key === "Enter" && verifyOtp()} />
                )}
                <button onClick={otpSent ? verifyOtp : sendOtp} disabled={busy}
                        className="btn-gold mt-3 w-full">
                  {busy ? "…" : otpSent ? t("verify_code") : t("send_code")}
                </button>
              </>
            )}
            {msg && <p className="mt-3 text-center text-xs text-[var(--warn)]">{msg}</p>}
          </div>
        </div>
      )}
    </>
  );
}
