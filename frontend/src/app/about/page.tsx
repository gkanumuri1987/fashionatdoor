"use client";

/** About — the story, the standard, and the sign-up. Marketing voice, but
 *  every claim on this page is verifiably true of the product. */

import { useState } from "react";
import AuthBar from "@/components/AuthBar";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

const STATS: [string, string][] = [
  ["345+", "automated correctness tests"],
  ["1″", "arc-second planetary precision"],
  ["9", "countries & timezones served"],
  ["3", "languages — English · తెలుగు · हिन्दी"],
  ["15", "divisional charts, D1–D60"],
  ["7", "dasha systems incl. Kalachakra"],
];

const PILLARS: [string, string, string][] = [
  ["🔭", "Astronomy first, always",
   "Every position comes from the Swiss Ephemeris — the same engine trusted by professional astrologers worldwide — computed to arc-second precision with historically correct timezones back to the 1800s. Our AI is never allowed to guess a degree, a date, or a dasha. It cannot: the architecture physically separates calculation from interpretation."],
  ["📜", "The classics, cited",
   "Readings are woven from freshly rendered classical dictums — Brihat Parashara Hora Shastra, Phaladeepika, Saravali, the Jaimini Sutras — each matched to your chart by rule, not by vibe. Tap any sentence and see its receipt: the exact chart condition and source that produced it. No other astrology app shows its work like this."],
  ["⚖️", "Strength decides, like a real jyotishi",
   "We compute full Shadbala, Ashtakavarga with shodhana, avasthas and functional lordships — so a yoga on a strong planet reads differently from the same yoga on a weak one. That judgment layer is what separates software that lists placements from software that understands them."],
  ["🌏", "Built for the diaspora",
   "A tithi that ends at dawn in Hyderabad ended the previous evening in New York. Our panchanga calendar and festival dates are computed at YOUR sunrise — India, US, UK, Gulf, Singapore, Australia — never converted, so Deepavali lands on the right day wherever your family lives."],
  ["🪔", "Tradition with honesty",
   "When your birth time is approximate, we say which results wobble and which stand firm. When schools differ — ayanamsas, Kalachakra variants — we name our convention. We never predict death, never frighten, never upsell fear. Remedies come from the Puranic tradition: your own Ishta Devata, computed from your karakamsa."],
  ["🔓", "Open and yours",
   "Our entire engine is open source — anyone can audit every formula. Your data stays yours on every plan; palm photos and floor plans are analyzed in memory and never stored."],
];

const FEATURES = [
  "Kundli — North & South styles, all vargas, yogas with strength scores",
  "AI life readings with receipts, in your language",
  "Ask anything — an assistant grounded in YOUR chart's real dasha dates",
  "Kundli Milan — 36 gunas + Dashakoota + honest Manglik analysis",
  "Panchanga & festival calendar — printable, timezone-true",
  "Varshaphal, KP, Jaimini, Muhurta electional picks",
  "Palmistry by shareable link · Vastu from a floor-plan photo",
];

export default function AboutPage() {
  const { t } = useLang();
  const sb = supabase();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [err, setErr] = useState("");

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
      <header className="text-center">
        <h1 className="heading-display text-5xl">{t("app_title")}</h1>
        <div className="ornament mt-3 text-xs">✦</div>
        <p className="mx-auto mt-4 max-w-2xl text-lg leading-relaxed text-[var(--ink-soft)]">
          The world&apos;s most rigorously computed Vedic astrology platform —
          where five millennia of Jyotisha meet arc-second astronomy, and
          <span className="text-[var(--gold)]"> nothing is ever guessed.</span>
        </p>
      </header>

      {/* Stats band */}
      <section className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {STATS.map(([n, l]) => (
          <div key={l} className="card p-4 text-center">
            <div className="heading-display text-3xl">{n}</div>
            <div className="mt-1 text-xs text-[var(--ink-muted)]">{l}</div>
          </div>
        ))}
      </section>

      {/* The difference */}
      <section className="mt-12 space-y-4">
        <h2 className="heading-section text-center text-2xl">Why families across the world choose us</h2>
        {PILLARS.map(([icon, title, body]) => (
          <div key={title} className="card p-5">
            <h3 className="font-semibold text-[var(--gold)]">{icon} {title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-[var(--ink-soft)]">{body}</p>
          </div>
        ))}
      </section>

      {/* Everything inside */}
      <section className="mt-12">
        <h2 className="heading-section text-center text-2xl">Everything a family panchangam shelf holds — in one place</h2>
        <ul className="mx-auto mt-4 max-w-2xl space-y-2 text-sm text-[var(--ink-soft)]">
          {FEATURES.map((f) => (
            <li key={f} className="flex gap-2"><span className="text-[var(--good)]">✓</span>{f}</li>
          ))}
        </ul>
      </section>

      {/* Sign-up CTA */}
      <section className="card mx-auto mt-12 max-w-xl p-8 text-center">
        <h2 className="heading-display text-3xl">{t("about_join_title")}</h2>
        <p className="mt-3 text-sm leading-relaxed text-[var(--ink-soft)]">{t("about_join_body")}</p>
        {sent ? (
          <p className="mt-5 text-sm text-[var(--good)]">✓ {t("code_sent")}</p>
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
        {sent && (
          <div className="mt-4 flex justify-center"><AuthBar /></div>
        )}
      </section>

      <footer className="mt-12 text-center text-xs text-[var(--ink-muted)]">
        {t("disclaimer")}
      </footer>
    </main>
  );
}
