"use client";

/** Landing — the story of the app, told to spark curiosity and excitement.
 *  Every capability named here exists and works; nothing promised that the
 *  product cannot do today. */

import Link from "next/link";
import { useState } from "react";
import { useEffect } from "react";
import AuthBar from "@/components/AuthBar";
import Icon, { type IconName } from "@/components/Icon";
import { JaathakaMark } from "@/components/Logo";
import { captureReferralParam, claimPendingReferral, useAccount } from "@/lib/account";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

const ROTATING_QUESTIONS = [
  "When will I marry — and who is written for me?",
  "Which years will lift my career?",
  "What does my chart say about children?",
  "Which deity is mine, by my own birth stars?",
];

// Browser timezone → the calendar API's location keys.
function tzToLocation(): string {
  try {
    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
    if (tz.includes("Kolkata") || tz.includes("Calcutta")) return "in";
    if (tz === "Europe/London") return "uk";
    if (tz === "America/New_York" || tz.includes("Toronto")) return "us_east";
    if (tz === "America/Chicago") return "us_central";
    if (tz.includes("Los_Angeles") || tz.includes("Vancouver")) return "us_west";
    if (tz.startsWith("Australia")) return "au";
    if (tz === "Asia/Dubai") return "gulf";
    if (tz === "Asia/Singapore" || tz === "Asia/Kuala_Lumpur") return "sg";
    if (tz.startsWith("America")) return "us_east";
    if (tz.startsWith("Europe")) return "uk";
  } catch { /* default below */ }
  return "in";
}

interface SkyDay {
  date: string; vara: string; vara_local?: string;
  tithi: { name: string; local?: string; ends: string | null };
  nakshatra: { name: string; local?: string; ends: string | null };
  masa_local?: string; masa: string; moon_phase?: "full" | "new" | null;
  good_time?: { abhijit: string | null };
  avoid_times?: { rahu_kalam: string | null };
}

const CAPABILITIES: [IconName, string, string, string][] = [
  ["chart", "Your complete jaathakam, in minutes",
   "Birth date, time, place — and your full kundli appears: North or South style, every planet, every nakshatra, your dashas mapped across your whole life with real dates.",
   "/kundli"],
  ["chat", "Talk to your jaathakam",
   "Ask it anything, in Telugu, Hindi or English — marriage, career, children, 'summarize my life'. The answers come from YOUR chart's actual planetary periods, with the dates to prove it. It feels like sitting with a learned family jyotishi who has studied your chart for hours.",
   "/kundli"],
  ["match", "Marriage matching the full traditional way",
   "All 36 gunas, the southern Dashakoota checks, honest Manglik analysis with its classical exceptions — and a warm reading of what the match truly holds.",
   "/match"],
  ["calendar", "Your family's festival calendar — wherever you live",
   "Ugadi, Deepavali, Varalakshmi Vratam on the RIGHT day for Dallas, London, Sydney or Hyderabad — with tithis, good times and Rahu kalam in your own clock, in your own script. Print it, pin it, share it.",
   "/calendar"],
  ["palm", "Palm reading by a simple link",
   "Send a link to anyone — they photograph their palm and the reading appears right there. Lines, mounts, hand shape — read honestly, never invented.",
   "/palmistry"],
  ["vastu", "Vastu from a floor-plan photo",
   "Upload your home's plan, tell us which way it faces — every room is judged by the classical placement rules, with practical remedies where something sits wrong.",
   "/vastu"],
];

// How Jaathaka is different from every other astrology app — point by point.
// [icon, title, what most apps do, what Jaathaka does]
const DIFFERENTIATORS: [IconName, string, string, string][] = [
  ["chart", "Real astronomy, not a chatbot's guess",
   "Most AI astrology apps ask a language model for your planets — and it quietly invents them, so every prediction is built on fiction.",
   "We compute your planets with Swiss Ephemeris — the same professional astronomy temples use — exact to the arc-second. The AI is handed those facts and is blocked from ever stating a position or date it wasn't given."],
  ["about", "The shastra, rule by rule",
   "Others generate generic sun-sign horoscope prose that could fit anyone.",
   "Your reading is matched dictum by dictum to hand-authored classical rules — Brihat Parashara Hora Shastra, Phaladeepika, Saravali, Jaimini — each cited by source and specific to YOUR chart."],
  ["calendar", "Timing from your real dashas",
   "A vague “good things are coming” with no actual when.",
   "Every “when will I…” answer is a Vimshottari dasha window with real start and end dates computed from your Moon — the dates to prove it."],
  ["vastu", "Your city, your clock — to the minute",
   "One-size-fits-India timings, or a wrong Rahu kalam once you live abroad.",
   "Panchanga is computed at your exact coordinates and your place's historical timezone (correct even for a 1940s birth), so Rahu kalam is right in Dallas or Hyderabad — and a good time is never shown overlapping a bad one."],
  ["plans", "Personal remedies, honest reasons",
   "Fear-driven doshas and paid pooja / gemstone upsells.",
   "Your Ishta Devata is computed from your own karakamsa, and every parihaaram carries a real behavioural or circadian reason — never fear, never a sales pitch."],
  ["palm", "Palmistry & Vastu, the same rigour",
   "AI “reads” a palm or floor plan by imagining what might be there.",
   "Vision only extracts what is actually visible; classical Hasta Samudrika (palm) and Vastu placement rules do the judging; the AI only narrates — and refuses an unclear photo instead of inventing."],
  ["chat", "Honesty, built in",
   "Apps that will confidently tell you when you'll die or what disease you'll get.",
   "Jaathaka never predicts death or lifespan, never diagnoses illness, never gives investment tips — and says plainly when your birth time is uncertain."],
  ["account", "Yours, and private",
   "Your data mined, your reading forgotten the moment you close the tab.",
   "Every jaathakam — yours and your family's — is saved to your account, in English, Telugu or Hindi, and your palm photo is analysed in memory and never stored."],
];

const SOURCES = ["Brihat Parashara Hora Shastra", "Phaladeepika", "Saravali",
                 "Jaimini Sutras", "Brihat Jataka", "Tajika Nilakanthi",
                 "the Puranas & epics"];

export default function LandingPage() {
  const { lang, t } = useLang();
  const { signedIn } = useAccount();
  const sb = supabase();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState("");
  const [sky, setSky] = useState<SkyDay | null>(null);
  const [skyLoc, setSkyLoc] = useState("");
  const [qIdx, setQIdx] = useState(0);
  const [qFade, setQFade] = useState(true);

  useEffect(() => {
    captureReferralParam();
    claimPendingReferral();
  }, []);

  // Live sky for the visitor's own timezone — real computation, real proof.
  useEffect(() => {
    const now = new Date();
    const loc = tzToLocation();
    const tradition = lang === "hi" ? "hindi" : "telugu";
    fetch("/api/calendar", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ year: now.getFullYear(), month: now.getMonth() + 1,
                             tradition, location: loc }),
    }).then((r) => (r.ok ? r.json() : null)).then((m) => {
      if (!m) return;
      const today = now.toISOString().slice(0, 10);
      const d = m.days.find((x: SkyDay) => x.date === today) ?? m.days[now.getDate() - 1];
      if (d) { setSky(d); setSkyLoc(m.location); }
    }).catch(() => {});
  }, [lang]);

  // Softly rotating curiosity line.
  useEffect(() => {
    const id = setInterval(() => {
      setQFade(false);
      setTimeout(() => {
        setQIdx((i) => (i + 1) % ROTATING_QUESTIONS.length);
        setQFade(true);
      }, 400);
    }, 4200);
    return () => clearInterval(id);
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
        <div className="mb-4 flex justify-center"><JaathakaMark size={64} /></div>
        <p className="text-xs uppercase tracking-[0.3em] text-[var(--gold)]">
          జాతక · जातक · Jaathaka
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
          <Link href="/kundli" className="btn-gold inline-flex items-center gap-2 text-base">
            <Icon name="chart" className="h-[18px] w-[18px]" /> Reveal my jaathakam
          </Link>
          <Link href={signedIn ? "/profile" : "/subscription"} className="btn-ghost inline-flex items-center gap-2 text-base">
            <Icon name={signedIn ? "account" : "plans"} className="h-[18px] w-[18px]" />
            {signedIn ? "My account" : "See plans"}
          </Link>
        </div>
      </header>

      {/* ── Today's sky — computed live for the visitor's own timezone ── */}
      {sky && (
        <section className="mt-14">
          <div className="card mx-auto max-w-2xl overflow-hidden p-0">
            <div className="flex items-center justify-between border-b border-[var(--line-soft)] bg-[var(--gold)]/8 px-5 py-2.5">
              <span className="text-xs font-semibold uppercase tracking-widest text-[var(--gold)]">
                ● Today&apos;s sky — computed live
              </span>
              <span className="text-[10px] text-[var(--ink-faint)]">{skyLoc}</span>
            </div>
            <div className="grid grid-cols-2 gap-4 px-5 py-4 text-center sm:grid-cols-4">
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--ink-faint)]">Tithi</div>
                <div className="mt-0.5 text-sm text-[var(--ink)]">
                  {sky.tithi.local ?? sky.tithi.name}
                  {sky.moon_phase === "full" && " 🌕"}{sky.moon_phase === "new" && " 🌑"}
                </div>
                {sky.tithi.ends && <div className="text-[10px] text-[var(--ink-muted)]">till {sky.tithi.ends}</div>}
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--ink-faint)]">Nakshatra</div>
                <div className="mt-0.5 text-sm text-[var(--ink)]">{sky.nakshatra.local ?? sky.nakshatra.name}</div>
                {sky.nakshatra.ends && <div className="text-[10px] text-[var(--ink-muted)]">till {sky.nakshatra.ends}</div>}
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--ink-faint)]">Good time</div>
                <div className="mt-0.5 text-sm text-[var(--good)]">✓ {sky.good_time?.abhijit ?? "—"}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-wider text-[var(--ink-faint)]">Rahu kalam</div>
                <div className="mt-0.5 text-sm text-[var(--bad)]">✗ {sky.avoid_times?.rahu_kalam ?? "—"}</div>
              </div>
            </div>
          </div>
          <p className="mx-auto mt-5 max-w-xl text-center text-base leading-relaxed text-[var(--ink-soft)]">
            This is today, read from the real sky over <span className="text-[var(--gold)]">your</span> city.
            Your birth minute had a sky of its own —
            <span className={`block pt-1 text-[var(--gold)] transition-opacity duration-500 ${qFade ? "opacity-100" : "opacity-0"}`}>
              “{ROTATING_QUESTIONS[qIdx]}” — it already holds the answer.
            </span>
          </p>
        </section>
      )}

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

      {/* ── Ayanamsa deep guide ── */}
      <section id="ayanamsa" className="card mt-14 scroll-mt-24 p-6">
        <h2 className="heading-section text-2xl">{t("ay_section_title")}</h2>
        <p className="mt-3 text-sm leading-relaxed text-[var(--ink-soft)]">{t("ay_section_intro")}</p>
        <div className="mt-5 space-y-3">
          {([
            [true, "Lahiri (Chitrapaksha)", "ay_lahiri", true],
            [false, "Raman", "ay_raman", false],
            [false, "KP (Krishnamurti)", "ay_kp", false],
            [true, "True Chitrapaksha", "ay_true_citra", false],
            [true, "True Pushya", "ay_true_pushya", false],
            [true, "Yukteshwar", "ay_yukteshwar", false],
          ] as [boolean, string, string, boolean][]).map(([mark, name, key, rec]) => (
            <div key={name} className={`rounded-lg border p-4 ${rec ? "border-[var(--line-gold)] bg-[var(--gold)]/6" : "border-[var(--line-soft)]"}`}>
              <h3 className="flex items-center font-semibold text-[var(--gold)]">
                {mark && <Icon name="sparkle" className="mr-1.5 h-3.5 w-3.5" />}{name}
                {rec && <span className="ml-2 rounded-full bg-[var(--gold)] px-2 py-0.5 text-[10px] text-[var(--on-gold)]">{t("recommended")}</span>}
              </h3>
              <p className="mt-1.5 text-sm leading-relaxed text-[var(--ink-soft)]">{t(key)}</p>
            </div>
          ))}
        </div>
        <p className="mt-4 text-sm text-[var(--good)]">✓ {t("ay_recommend")}</p>
      </section>

      {/* ── Why Jaathaka is different — point by point ── */}
      <section className="mt-14">
        <h2 className="heading-section text-center text-2xl">What makes Jaathaka unlike any other</h2>
        <p className="mx-auto mt-3 max-w-2xl text-center text-sm leading-relaxed text-[var(--ink-soft)]">
          Most astrology apps are a chatbot dressed in a starfield. Jaathaka is a
          real Jyotish engine with a scholar-jyotishi's discipline. Here is the
          difference — each and every one.
        </p>
        <div className="mt-6 space-y-3">
          {DIFFERENTIATORS.map(([icon, title, others, ours]) => (
            <div key={title} className="card p-5">
              <h3 className="flex items-center gap-3 font-semibold text-[var(--gold)]">
                <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-[var(--line-gold)] bg-[var(--gold)]/8 text-[var(--gold)]">
                  <Icon name={icon} className="h-4 w-4" />
                </span>
                {title}
              </h3>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg border border-[var(--line-soft)] p-3 text-sm">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--ink-faint)]">Most apps</div>
                  <p className="mt-1 text-[var(--ink-muted)]">{others}</p>
                </div>
                <div className="rounded-lg border border-[var(--line-gold)] bg-[var(--gold)]/6 p-3 text-sm">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-[var(--gold)]">Jaathaka</div>
                  <p className="mt-1 text-[var(--ink-soft)]">{ours}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Everything it does ── */}
      <section className="mt-14">
        <h2 className="heading-section text-center text-2xl">Everything inside</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          {CAPABILITIES.map(([icon, title, body, href]) => (
            <Link key={title} href={href}
                  className="card group block p-5 transition-transform hover:-translate-y-0.5">
              <h3 className="flex items-start gap-3 font-semibold text-[var(--gold)]">
                <span className="mt-0.5 grid h-9 w-9 shrink-0 place-items-center rounded-full border border-[var(--line-gold)] bg-[var(--gold)]/8 text-[var(--gold)] transition-colors group-hover:bg-[var(--gold)]/14">
                  <Icon name={icon} className="h-[18px] w-[18px]" />
                </span>
                <span className="pt-1.5">{title}</span>
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">{body}</p>
            </Link>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-[var(--ink-muted)]">
          Plus: Varshaphal year charts · KP & Jaimini for practitioners · Muhurta good-day
          finder · everything in English, తెలుగు and हिन्दी.
        </p>
      </section>

      {/* ── Plans teaser (guests only) ── */}
      {!signedIn && (
      <section className="card mt-14 border-[var(--line-gold)] p-6 text-center">
        <h2 className="heading-display text-3xl">Your first jaathakam is free.</h2>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-[var(--ink-soft)]">
          Save it to your account forever. When you&apos;re ready for more — the whole
          family&apos;s jaathakams, unlimited questions to the AI jyotishi — plans start
          at just <b className="text-[var(--gold)]">$1.99 / ₹179 a month</b>, with a
          once-and-forever Lifetime option. Share your link with friends and earn
          free questions every time someone joins.
        </p>
        <Link href="/subscription" className="btn-gold mt-5 inline-flex items-center gap-2">
          <Icon name="plans" className="h-[18px] w-[18px]" /> Explore plans
        </Link>
      </section>
      )}

      {/* ── Sign-up (guests only) ── */}
      {!signedIn && (
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
      )}

      <footer className="mt-14 text-center text-xs text-[var(--ink-muted)]">
        {t("disclaimer")}
      </footer>
    </main>
  );
}
