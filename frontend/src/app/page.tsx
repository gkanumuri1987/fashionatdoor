"use client";

/** Landing — the story of the app, told to spark curiosity and excitement.
 *  Every capability named here exists and works; nothing promised that the
 *  product cannot do today. */

import Link from "next/link";
import { useState } from "react";
import { useEffect } from "react";
import AuthBar from "@/components/AuthBar";
import { captureReferralParam, claimPendingReferral } from "@/lib/account";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

const QUESTIONS = [
  "When will I marry — and what kind of partner is written for me?",
  "Which years will lift my career, and which ask for patience?",
  "What does my chart say about children?",
  "Is this match right for our family?",
  "Which deity is MINE to worship — by my own birth stars?",
];

const CAPABILITIES: [string, string, string, string][] = [
  ["✧", "Your complete jaathakam, in minutes",
   "Birth date, time, place — and your full kundli appears: North or South style, every planet, every nakshatra, your dashas mapped across your whole life with real dates.",
   "/kundli"],
  ["🗨", "Talk to your jaathakam",
   "Ask it anything, in Telugu, Hindi or English — marriage, career, children, 'summarize my life'. The answers come from YOUR chart's actual planetary periods, with the dates to prove it. It feels like sitting with a learned family jyotishi who has studied your chart for hours.",
   "/kundli"],
  ["❋", "Marriage matching the full traditional way",
   "All 36 gunas, the southern Dashakoota checks, honest Manglik analysis with its classical exceptions — and a warm reading of what the match truly holds.",
   "/match"],
  ["🗓", "Your family's festival calendar — wherever you live",
   "Ugadi, Deepavali, Varalakshmi Vratam on the RIGHT day for Dallas, London, Sydney or Hyderabad — with tithis, good times and Rahu kalam in your own clock, in your own script. Print it, pin it, share it.",
   "/calendar"],
  ["✋", "Palm reading by a simple link",
   "Send a link to anyone — they photograph their palm and the reading appears right there. Lines, mounts, hand shape — read honestly, never invented.",
   "/palmistry"],
  ["⌂", "Vastu from a floor-plan photo",
   "Upload your home's plan, tell us which way it faces — every room is judged by the classical placement rules, with practical remedies where something sits wrong.",
   "/vastu"],
];

const SOURCES = ["Brihat Parashara Hora Shastra", "Phaladeepika", "Saravali",
                 "Jaimini Sutras", "Brihat Jataka", "Tajika Nilakanthi",
                 "the Puranas & epics"];

export default function LandingPage() {
  const { t } = useLang();
  const sb = supabase();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    captureReferralParam();
    claimPendingReferral();
  }, []);

  async function signup() {
    if (!sb || !email.trim()) return;
    setErr("");
    const { error } = await sb.auth.signInWithOtp({
      email: email.trim(), options: { shouldCreateUser: true },
    });
    if (error) { setErr(error.message); return; }
    setSent(true);
  }

  return (
    <main className="mx-auto max-w-4xl px-4 py-12">
      {/* ── Hero: curiosity ── */}
      <header className="text-center">
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--gold)]">
          జ్యోతిషం · ज्योतिष · Jyotisha
        </p>
        <h1 className="heading-display mt-3 text-5xl leading-tight">
          The sky remembers the minute you were born.
        </h1>
        <div className="ornament mt-4 text-xs">✦</div>
        <p className="mx-auto mt-4 max-w-2xl text-lg leading-relaxed text-[var(--ink-soft)]">
          At that exact moment, nine grahas stood in a pattern that has never
          repeated and never will. Our rishis spent five thousand years learning
          to read that pattern. <span className="text-[var(--gold)]">Now it
          takes you two minutes to see yours.</span>
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link href="/kundli" className="btn-gold text-base">✧ Reveal my jaathakam</Link>
          <Link href="/subscription" className="btn-ghost text-base">✦ See plans</Link>
        </div>
      </header>

      {/* ── The questions it answers ── */}
      <section className="mt-14">
        <h2 className="heading-section text-center text-2xl">
          The questions you&apos;ve always wanted to ask
        </h2>
        <div className="mt-5 space-y-2">
          {QUESTIONS.map((q) => (
            <div key={q} className="card px-4 py-3 text-sm text-[var(--ink-soft)]">
              <span className="mr-2 text-[var(--gold)]">❝</span>{q}
            </div>
          ))}
        </div>
        <p className="mt-4 text-center text-sm text-[var(--ink-muted)]">
          Your jaathakam has been holding the answers all along — now you can ask it directly,
          and it replies with <span className="text-[var(--gold)]">your real planetary periods and their dates</span>.
        </p>
      </section>

      {/* ── Accuracy & scriptures ── */}
      <section className="card mt-14 p-6">
        <h2 className="heading-section text-2xl">Why our answers can be trusted</h2>
        <p className="mt-3 text-sm leading-relaxed text-[var(--ink-soft)]">
          Two things make a jaathakam true: the <b className="text-[var(--ink)]">sky</b> and
          the <b className="text-[var(--ink)]">shastra</b>. For the sky, we compute your
          planets with the same professional-grade astronomy that powers the
          panchangams in temples — exact to the arc-second, with your birth
          place&apos;s historical clock handled correctly even for the 1940s. For
          the shastra, our readings are drawn from deeply researched classical
          works — {SOURCES.slice(0, -1).join(", ")} and {SOURCES.at(-1)} — matched
          to your chart rule by rule, the way a scholar-jyotishi was trained to.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-[var(--ink-soft)]">
          Even your <span className="text-[var(--gold)]">remedies are personal</span>:
          from your own karakamsa we compute your Ishta Devata — the deity the
          Jaimini tradition says is yours — and the strengthening practices the
          Puranas prescribe for each graha: Hanuman for Shani, Ganesha for Ketu,
          Durga for Rahu.
        </p>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">
          And when a detail is uncertain — an approximate birth time, a boundary
          degree — we tell you plainly instead of pretending. That honesty is why
          people trust what we say when it matters.
        </p>
      </section>

      {/* ── Everything it does ── */}
      <section className="mt-14">
        <h2 className="heading-section text-center text-2xl">Everything inside</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {CAPABILITIES.map(([icon, title, body, href]) => (
            <Link key={title} href={href}
                  className="card block p-5 transition-transform hover:-translate-y-0.5">
              <h3 className="font-semibold text-[var(--gold)]">{icon} {title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">{body}</p>
            </Link>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-[var(--ink-muted)]">
          Plus: Varshaphal year charts · KP & Jaimini for practitioners · Muhurta good-day
          finder · everything in English, తెలుగు and हिन्दी.
        </p>
      </section>

      {/* ── Plans teaser ── */}
      <section className="card mt-14 border-[var(--line-gold)] p-6 text-center">
        <h2 className="heading-display text-3xl">Your first jaathakam is free.</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-[var(--ink-soft)]">
          Save it to your account forever. When you&apos;re ready for more — the whole
          family&apos;s jaathakams, unlimited questions to the AI jyotishi — plans start
          at just <b className="text-[var(--gold)]">$1.99 / ₹179 a month</b>, with a
          once-and-forever Lifetime option. Share your link with friends and earn
          free questions every time someone joins.
        </p>
        <Link href="/subscription" className="btn-gold mt-5 inline-flex">✦ Explore plans</Link>
      </section>

      {/* ── Sign-up ── */}
      <section className="mx-auto mt-14 max-w-xl text-center">
        <h2 className="heading-display text-3xl">{t("about_join_title")}</h2>
        <p className="mt-3 text-sm leading-relaxed text-[var(--ink-soft)]">{t("about_join_body")}</p>
        {sent ? (
          <>
            <p className="mt-5 text-sm text-[var(--good)]">✓ {t("code_sent")}</p>
            <div className="mt-4 flex justify-center"><AuthBar /></div>
          </>
        ) : (
          <form className="mx-auto mt-5 flex max-w-sm gap-2"
                onSubmit={(e) => { e.preventDefault(); signup(); }}>
            <input type="email" required value={email}
                   onChange={(e) => setEmail(e.target.value)}
                   placeholder="you@example.com" className="input flex-1" />
            <button type="submit" className="btn-gold">{t("about_join_btn")}</button>
          </form>
        )}
        {err && <p className="mt-2 text-xs text-red-400">{err}</p>}
      </section>

      <footer className="mt-14 text-center text-xs text-[var(--ink-muted)]">
        {t("disclaimer")}
      </footer>
    </main>
  );
}
