"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

/** Sign-in state + email OTP login, rendered in the page header.
 *  Renders nothing when Supabase env vars are absent. */
export default function AuthBar() {
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
    setMsg("Code sent — check your email.");
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
        <span className="text-[#9c8f6f]">{userEmail}</span>
        <button
          onClick={() => sb.auth.signOut()}
          className="rounded-md border border-[#3d2f5c] px-3 py-1 hover:bg-[#2a1d45]"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div className="relative text-sm">
      <button
        onClick={() => setOpen((o) => !o)}
        className="rounded-md bg-[#c9a227] px-4 py-1.5 text-[#140b26] font-semibold hover:bg-[#b08e1f]"
      >
        Sign in
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-72 rounded-lg border border-[#3d2f5c] bg-[#1a1030] p-4 shadow-lg">
          <p className="mb-2 font-medium">Sign in with email</p>
          <input
            type="email" value={email} placeholder="you@example.com"
            onChange={(e) => setEmail(e.target.value)}
            className="mb-2 w-full rounded-md border border-[#3d2f5c] bg-[#140b26] px-3 py-1.5 text-[#e8e0cc]"
            disabled={otpSent}
          />
          {otpSent && (
            <input
              value={otp} placeholder="6-digit code"
              onChange={(e) => setOtp(e.target.value)}
              className="mb-2 w-full rounded-md border border-[#3d2f5c] bg-[#140b26] px-3 py-1.5 text-[#e8e0cc]"
            />
          )}
          <button
            onClick={otpSent ? verifyOtp : sendOtp} disabled={busy}
            className="w-full rounded-md bg-[#c9a227] py-1.5 text-[#140b26] font-semibold hover:bg-[#b08e1f] disabled:opacity-50"
          >
            {busy ? "…" : otpSent ? "Verify code" : "Send code"}
          </button>
          {msg && <p className="mt-2 text-xs text-[#9c8f6f]">{msg}</p>}
        </div>
      )}
    </div>
  );
}
