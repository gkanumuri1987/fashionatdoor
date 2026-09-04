/** Privacy & data policy — truthful to how the app actually handles data.
 *  Kept plain English (a legal document); the app UI localizes elsewhere. */

import Link from "next/link";

export const metadata = {
  title: "Privacy & Data — Jaathaka",
  description: "What Jaathaka stores, who processes it, and how long it is kept.",
};

const REPO = "https://github.com/gkanumuri1987/fashionatdoor";

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="heading-display text-4xl">Privacy &amp; Data</h1>
      <p className="mt-2 text-sm text-[var(--ink-faint)]">Last updated: this reflects current behaviour.</p>

      <div className="mt-8 space-y-6 text-sm leading-relaxed text-[var(--ink-soft)]">
        <section>
          <h2 className="heading-section text-xl text-[var(--ink)]">What we store</h2>
          <p className="mt-2">
            To compute a jaathakam we store the birth details you enter — name,
            date, time and place of birth (as coordinates and timezone) — under
            your account, plus the charts and readings you generate and a record
            of your logins. This is personal data; it is kept only to provide the
            service to you, is secured per-account (row-level security so no other
            user can read it), and is never sold or shared for advertising.
          </p>
        </section>

        <section>
          <h2 className="heading-section text-xl text-[var(--ink)]">Who processes it</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li><b className="text-[var(--ink)]">Supabase</b> — authentication and the database that holds your account data.</li>
            <li><b className="text-[var(--ink)]">Google (Gemini)</b> — the AI that writes readings, chat answers and palm/vastu analyses receives the computed chart facts (and, for palmistry/vastu, the uploaded image) to generate text. The astronomical calculations themselves run on our own server and use no AI.</li>
            <li><b className="text-[var(--ink)]">Stripe / Razorpay</b> — if you subscribe, the payment is processed by the gateway you choose. We never see or store your card details.</li>
          </ul>
        </section>

        <section>
          <h2 className="heading-section text-xl text-[var(--ink)]">Palmistry &amp; floor-plan photos</h2>
          <p className="mt-2">
            Palm and vastu images are processed <b className="text-[var(--ink)]">in memory only</b>: the photo is analysed and then discarded — we keep only the derived text reading, never the image. A palm-reading link expires within 48 hours, and any leftover session data is swept automatically.
          </p>
        </section>

        <section>
          <h2 className="heading-section text-xl text-[var(--ink)]">Your control</h2>
          <p className="mt-2">
            You can delete any saved profile or chart from your account at any
            time. To delete your account entirely, contact us and we will remove
            your data.
          </p>
        </section>

        <section>
          <h2 className="heading-section text-xl text-[var(--ink)]">Not professional advice</h2>
          <p className="mt-2">
            Readings are offered for guidance and reflection. They are not a
            substitute for professional medical, legal, or financial advice, and
            the service never predicts death or lifespan, diagnoses illness, or
            gives investment instructions.
          </p>
        </section>

        <section>
          <h2 className="heading-section text-xl text-[var(--ink)]">Open source</h2>
          <p className="mt-2">
            Jaathaka is built on the Swiss Ephemeris and is released under the
            AGPL-3.0 licence. The complete source code of this service is
            published at{" "}
            <a href={REPO} target="_blank" rel="noopener noreferrer"
               className="text-[var(--gold)] underline">github.com/gkanumuri1987/fashionatdoor</a>.
          </p>
        </section>
      </div>

      <div className="mt-10">
        <Link href="/" className="text-sm text-[var(--gold)]">← Back to Jaathaka</Link>
      </div>
    </main>
  );
}
