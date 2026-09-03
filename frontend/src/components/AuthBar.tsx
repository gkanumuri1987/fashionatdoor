"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import { useLang } from "@/lib/i18n";

/** Sign-in state + email OTP login, rendered in the page header.
 *  Renders nothing when Supabase env vars are absent. */
export default function AuthBar() {
  const { t } = useLang();
  const sb = supabase();
  const [email, setEmail] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
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
    });
    return () => sub.subscription.unsubscribe();
  }, [sb]);

  if (!sb) return null;

  async function sendOtp() {
    if (!sb || !email.trim()) return;
    setBusy(true); setMsg("");
    const { error } = await sb.auth.signInWithOtp({
      email: email.trim(),
      options: { shouldCreateUser: true },
    });
    setBusy(false);
    if (error) { setMsg(error.message); return; }
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
    if (error) { setMsg(error.message); return; }
    setOpen(false); setOtpSent(false); setOtp("");
  }

  if (userEmail) {
    return (
      <div className="flex items-center gap-3 text-sm">
        <span className="text-[var(--ink-muted)]">{userEmail}</span>
        <button
          onClick={() => sb.auth.signOut()}
          className="rounded-md border border-[var(--line)] px-3 py-1 hover:bg-[var(--surface-raised)]"
        >{t("sign_out")}</button>
      </div>
    );
  }

  return (
    <div className="relative text-sm">
      <button
        onClick={() => setOpen((o) => !o)}
        className="rounded-md bg-[var(--gold)] px-4 py-1.5 text-[var(--on-gold)] font-semibold hover:bg-[var(--gold-bright)]"
      >{t("sign_in")}</button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-lg border border-[var(--line)] bg-[var(--surface-solid)] p-4 shadow-lg">
          <p className="mb-2 font-medium">{t("sign_in_email")}</p>
          <input
            type="email" value={email} placeholder="you@example.com"
            onChange={(e) => setEmail(e.target.value)}
            className="mb-2 w-full rounded-md border border-[var(--line)] bg-[var(--surface-deep)] px-3 py-1.5 text-[var(--ink)]"
            disabled={otpSent}
          />
          {otpSent && (
            <input
              value={otp} placeholder={t("code_ph")}
              onChange={(e) => setOtp(e.target.value)}
              className="mb-2 w-full rounded-md border border-[var(--line)] bg-[var(--surface-deep)] px-3 py-1.5 text-[var(--ink)]"
            />
          )}
          <button
            onClick={otpSent ? verifyOtp : sendOtp} disabled={busy}
            className="w-full rounded-md bg-[var(--gold)] py-1.5 text-[var(--on-gold)] font-semibold hover:bg-[var(--gold-bright)] disabled:opacity-50"
          >
            {busy ? "…" : otpSent ? t("verify_code") : t("send_code")}
          </button>
          {msg && <p className="mt-2 text-xs text-[var(--ink-muted)]">{msg}</p>}
        </div>
      )}
    </div>
  );
}
