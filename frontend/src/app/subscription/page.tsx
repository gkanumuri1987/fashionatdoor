"use client";

/** Subscription plans — plan choice is recorded per account (tracked in
 *  subscription_requests + user_flags); the payment step completes it once
 *  billing goes live. Premium unlocks unlimited saved jaathakams. */

import { useCallback, useEffect, useState } from "react";
import { useAccount } from "@/lib/account";
import { copyText } from "@/lib/clipboard";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

const PLANS = [
  {
    key: "monthly_basic", price: 1.99, inr: 179, period: "monthly" as const,
    features: ["plan_f_unlimited", "plan_f_readings", "plan_f_calendar"],
  },
  {
    key: "monthly_plus", price: 2.99, inr: 269, period: "monthly" as const, popular: true,
    features: ["plan_f_unlimited", "plan_f_readings", "plan_f_calendar",
               "plan_f_family", "plan_f_priority", "plan_f_ai"],
  },
  {
    key: "lifetime", price: 9.99, inr: 899, period: "lifetime" as const,
    features: ["plan_f_unlimited", "plan_f_readings", "plan_f_calendar",
               "plan_f_family", "plan_f_forever"],
  },
  {
    key: "lifetime_plus", price: 19.99, inr: 1799, period: "lifetime" as const,
    features: ["plan_f_unlimited", "plan_f_readings", "plan_f_calendar",
               "plan_f_family", "plan_f_priority", "plan_f_ai", "plan_f_forever"],
  },
];

interface Flags { plan?: string; is_premium?: boolean; plan_expires_at?: string | null }
interface SubReq { plan: string; status: string; created_at: string }

export default function SubscriptionPage() {
  const { t } = useLang();
  const sb = supabase();
  const [signedIn, setSignedIn] = useState<boolean | null>(null);
  const [flags, setFlags] = useState<Flags | null>(null);
  const [pending, setPending] = useState<SubReq | null>(null);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const { account } = useAccount();
  const [refCopied, setRefCopied] = useState(false);
  const [pay, setPay] = useState<{ stripe: boolean; razorpay: { enabled: boolean; key_id: string | null } } | null>(null);

  useEffect(() => {
    fetch("/api/pay/config").then((r) => (r.ok ? r.json() : null))
      .then(setPay).catch(() => setPay(null));
    const q = new URLSearchParams(window.location.search);
    if (q.get("paid")) setMsg(t("pay_success"));
    if (q.get("cancelled")) setMsg(t("pay_cancelled"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function payStripe(planKey: string) {
    if (!sb) return;
    const { data: u } = await sb.auth.getUser();
    if (!u.user) { setMsg(t("sub_signin_first")); return; }
    setBusy(planKey);
    try {
      const res = await fetch("/api/pay/stripe/checkout", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: planKey, user_id: u.user.id,
                               email: u.user.email ?? "", origin: window.location.origin }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);
      window.location.href = data.url;
    } catch (e) {
      setMsg(e instanceof Error ? e.message : t("generic_error"));
      setBusy("");
    }
  }

  async function payRazorpay(planKey: string) {
    if (!sb) return;
    const { data: u } = await sb.auth.getUser();
    if (!u.user) { setMsg(t("sub_signin_first")); return; }
    setBusy(planKey);
    try {
      if (!(window as unknown as { Razorpay?: unknown }).Razorpay) {
        await new Promise<void>((res, rej) => {
          const sc = document.createElement("script");
          sc.src = "https://checkout.razorpay.com/v1/checkout.js";
          sc.onload = () => res(); sc.onerror = () => rej(new Error("Razorpay load failed"));
          document.body.appendChild(sc);
        });
      }
      const res = await fetch("/api/pay/razorpay/order", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plan: planKey, user_id: u.user.id }),
      });
      const order = await res.json();
      if (!res.ok) throw new Error(order.detail);
      const RazorpayCtor = (window as unknown as { Razorpay: new (o: object) => { open: () => void } }).Razorpay;
      const rz = new RazorpayCtor({
        key: order.key_id, order_id: order.order_id,
        amount: order.amount, currency: order.currency, name: order.label,
        prefill: { email: u.user.email ?? "" },
        theme: { color: "#d9ab2e" },
        handler: async (resp: { razorpay_order_id: string; razorpay_payment_id: string; razorpay_signature: string }) => {
          const v = await fetch("/api/pay/razorpay/verify", {
            method: "POST", headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id: resp.razorpay_order_id,
                                   payment_id: resp.razorpay_payment_id,
                                   signature: resp.razorpay_signature,
                                   user_id: u.user!.id, plan: planKey }),
          });
          setMsg(v.ok ? t("pay_success") : t("generic_error"));
          refresh();
        },
      });
      rz.open();
      setBusy("");
    } catch (e) {
      setMsg(e instanceof Error ? e.message : t("generic_error"));
      setBusy("");
    }
  }

  const refresh = useCallback(async () => {
    if (!sb) return;
    const [{ data: f }, { data: r }] = await Promise.all([
      sb.from("user_flags").select("plan,is_premium,plan_expires_at").maybeSingle()
        .then((x) => x, () => ({ data: null })),
      sb.from("subscription_requests").select("plan,status,created_at")
        .order("created_at", { ascending: false }).limit(1).maybeSingle()
        .then((x) => x, () => ({ data: null })),
    ]);
    setFlags(f as Flags | null);
    setPending((r as SubReq | null)?.status === "pending" ? (r as SubReq) : null);
  }, [sb]);

  useEffect(() => {
    if (!sb) { setSignedIn(false); return; }
    sb.auth.getUser().then(({ data }) => {
      setSignedIn(Boolean(data.user));
      if (data.user) refresh();
    });
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      setSignedIn(Boolean(session?.user));
      if (session?.user) refresh();
    });
    return () => sub.subscription.unsubscribe();
  }, [sb, refresh]);

  const isPremium = Boolean(flags?.is_premium) ||
    (flags?.plan && flags.plan !== "free" &&
     (!flags.plan_expires_at || new Date(flags.plan_expires_at) > new Date()));

  async function choose(planKey: string, price: number, period: string) {
    if (!sb) return;
    const { data: u } = await sb.auth.getUser();
    if (!u.user) { setMsg(t("sub_signin_first")); return; }
    setBusy(planKey); setMsg("");
    const { error } = await sb.from("subscription_requests").insert({
      user_id: u.user.id, plan: planKey, price_usd: price, period,
    });
    setBusy("");
    if (error) {
      setMsg(error.code === "42P01"
        ? "Run db_migrations/003_subscriptions.sql in Supabase first."
        : error.message);
      return;
    }
    setMsg(t("sub_recorded"));
    refresh();
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-10">
      <header className="mb-8 text-center">
        <h1 className="heading-display text-4xl">{t("sub_title")}</h1>
        <div className="ornament mt-2 text-xs">✦</div>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">{t("sub_sub")}</p>
      </header>

      {isPremium && (
        <p className="card mx-auto mb-6 max-w-md p-4 text-center text-sm text-[var(--gold)]">
          ✦ {t("sub_active")} — {flags?.plan ?? "premium"}
        </p>
      )}
      {pending && !isPremium && (
        <p className="card mx-auto mb-6 max-w-md p-4 text-center text-xs text-[var(--ink-soft)]">
          ⏳ {t("sub_pending")} ({pending.plan})
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {PLANS.map((p) => (
          <div key={p.key}
               className={`card relative flex flex-col p-5 ${p.popular ? "border-[var(--line-gold)]" : ""}`}>
            {p.popular && (
              <span className="absolute -top-2.5 left-1/2 -translate-x-1/2 rounded-full bg-[var(--gold)] px-3 py-0.5 text-[10px] font-bold text-[var(--on-gold)]">
                {t("sub_popular")}
              </span>
            )}
            <h3 className="heading-section text-lg">{t(`plan_${p.key}`)}</h3>
            <div className="mt-2">
              <span className="font-display text-4xl font-semibold text-[var(--ink)]">${p.price}</span>
              <span className="text-sm text-[var(--ink-muted)]">
                {p.period === "monthly" ? t("sub_per_month") : t("sub_once")}
              </span>
              <div className="text-sm text-[var(--gold)]">
                ₹{p.inr}{p.period === "monthly" ? t("sub_per_month") : ""}
              </div>
            </div>
            <ul className="mb-4 mt-4 flex-1 space-y-2 text-sm text-[var(--ink-soft)]">
              {p.features.map((f) => (
                <li key={f} className="flex gap-2">
                  <span className="text-[var(--good)]">✓</span>{t(f)}
                </li>
              ))}
            </ul>
            {(pay?.stripe || pay?.razorpay.enabled) ? (
              <div className="space-y-2">
                {pay.razorpay.enabled && (
                  <button onClick={() => payRazorpay(p.key)}
                          disabled={busy !== "" || signedIn === false || Boolean(isPremium)}
                          className={p.popular ? "btn-gold w-full text-sm" : "btn-ghost w-full text-sm"}>
                    {busy === p.key ? "…" : t("pay_upi")}
                  </button>
                )}
                {pay.stripe && (
                  <button onClick={() => payStripe(p.key)}
                          disabled={busy !== "" || signedIn === false || Boolean(isPremium)}
                          className="btn-ghost w-full text-sm">
                    {busy === p.key ? "…" : `${t("pay_card")} — $${p.price}`}
                  </button>
                )}
              </div>
            ) : (
              <div className="w-full rounded-lg border border-dashed border-[var(--line)] py-2 text-center text-sm text-[var(--ink-muted)]">
                ⏳ {t("coming_soon")}
              </div>
            )}
          </div>
        ))}
      </div>

      {signedIn === false && (
        <p className="mt-6 text-center text-sm text-[var(--warn)]">{t("sub_signin_first")}</p>
      )}
      {msg && <p className="mt-4 text-center text-sm text-[var(--gold)]">{msg}</p>}

      <p className="mt-8 text-center text-xs text-[var(--ink-faint)]">{t("sub_note")}</p>

      {account && (
        <section id="account" className="card mx-auto mt-8 max-w-xl p-5">
          <h3 className="heading-section mb-3 text-lg">{t("acct_title")}</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-lg border border-[var(--line-soft)] p-3">
              <div className="text-xs text-[var(--ink-muted)]">{t("acct_plan")}</div>
              <div className="mt-0.5 capitalize text-[var(--gold)]">
                {(account.is_premium && account.plan === "free") ? "premium" : account.plan.replaceAll("_", " ")}
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
                <button
                  onClick={async () => setRefCopied(await copyText(`${window.location.origin}/?ref=${account.referral_code}`))}
                  className="btn-gold px-3 py-1 text-xs">
                  {refCopied ? t("copied") : t("copy")}
                </button>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}
