"use client";

/** Account state: plan, credits, referral code — via the my_account RPC
 *  (creates the flags row + referral code lazily, server-side). */

import { useCallback, useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

export interface Account {
  plan: string;
  is_premium: boolean;
  credits: number;
  referral_code: string | null;
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
      const { data } = await sb.rpc("my_account");
      const row = Array.isArray(data) ? data[0] : data;
      if (row) setAccount(row as Account);
    } catch { /* pre-migration: stays null */ }
  }, [sb]);

  useEffect(() => {
    if (!sb) { setSignedIn(false); return; }
    sb.auth.getUser().then(({ data }) => {
      setSignedIn(Boolean(data.user));
      if (data.user) refresh();
    });
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      setSignedIn(Boolean(session?.user));
      if (session?.user) refresh(); else setAccount(null);
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
