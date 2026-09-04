"use client";

/** Account state: plan, credits, referral code — via the my_account RPC
 *  (creates the flags row + referral code lazily, server-side). */

import { useCallback, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

/** The app owner is always Lifetime Plus. Recognised client-side so the account
 *  reflects it immediately (and independently of whether the one-time SQL grant
 *  has been run); migration 008 makes the same true server-side. */
export const OWNER_EMAIL = "kanumuri.choudary@gmail.com";

export interface Account {
  plan: string;
  is_premium: boolean;
  credits: number;
  referral_code: string | null;
  last_login_at?: string | null;
  login_count?: number;
}

export function chatUnlimited(a: Account | null): boolean {
  if (!a) return false;
  return a.is_premium || a.plan === "monthly_plus" || a.plan === "lifetime_plus";
}

export function useAccount() {
  const sb = supabase();
  const [account, setAccount] = useState<Account | null>(null);
  const [signedIn, setSignedIn] = useState<boolean | null>(null);

  const refresh = useCallback(async () => {
    if (!sb) return;
    try {
      const [{ data }, { data: u }] = await Promise.all([
        sb.rpc("my_account"),
        sb.auth.getUser(),
      ]);
      const row = Array.isArray(data) ? data[0] : data;
      const email = (u.user?.email ?? "").toLowerCase();
      let acct = (row as Account) ??
        { plan: "free", is_premium: false, credits: 0, referral_code: null };
      if (email && email === OWNER_EMAIL) {
        acct = { ...acct, plan: "lifetime_plus", is_premium: true };
      }
      setAccount(acct);
    } catch {
      // Pre-migration (my_account absent): the owner still sees Lifetime Plus.
      try {
        const { data: u } = await sb.auth.getUser();
        if ((u.user?.email ?? "").toLowerCase() === OWNER_EMAIL) {
          setAccount({ plan: "lifetime_plus", is_premium: true, credits: 999, referral_code: null });
        }
      } catch { /* stays null */ }
    }
  }, [sb]);

  useEffect(() => {
    if (!sb) { setSignedIn(false); return; }
    sb.auth.getUser().then(({ data }) => {
      setSignedIn(Boolean(data.user));
      if (data.user) refresh();
    });
    const { data: sub } = sb.auth.onAuthStateChange((event, session) => {
      setSignedIn(Boolean(session?.user));
      if (session?.user) {
        refresh();
        if (event === "SIGNED_IN") {
          // Stamp login activity once per real sign-in (best-effort).
          try {
            const ua = typeof navigator !== "undefined" ? navigator.userAgent.slice(0, 200) : "";
            sb.rpc("touch_login", { ua }).then(() => {}, () => {});
          } catch { /* pre-migration */ }
        }
      } else setAccount(null);
    });
    return () => sub.subscription.unsubscribe();
  }, [sb, refresh]);

  return { account, signedIn, refresh, sb };
}

/** Referral capture: remember ?ref= on landing; claim once after sign-in. */
export function captureReferralParam() {
  try {
    const ref = new URLSearchParams(window.location.search).get("ref");
    if (ref) localStorage.setItem("jyotish_ref", ref);
  } catch { /* ignore */ }
}

export async function claimPendingReferral(): Promise<void> {
  const sb = supabase();
  if (!sb) return;
  try {
    const code = localStorage.getItem("jyotish_ref");
    if (!code) return;
    const { data: u } = await sb.auth.getUser();
    if (!u.user) return;
    await sb.rpc("claim_referral", { code });
    localStorage.removeItem("jyotish_ref");
  } catch { /* best-effort */ }
}
