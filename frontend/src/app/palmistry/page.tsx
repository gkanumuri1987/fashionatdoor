"use client";

/** Palmistry link minting — its own page (moved from the home header).
 *  Creates a 48h tokenized link the user shares; the recipient photographs
 *  their palm and receives the reading on that link. */

import { useState } from "react";
import { copyText } from "@/lib/clipboard";
import { useLang } from "@/lib/i18n";

export default function PalmistryPage() {
  const { t } = useLang();
  const [palmLink, setPalmLink] = useState("");
  const [copied, setCopied] = useState<null | boolean>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function mint() {
    setBusy(true); setError("");
    try {
      const res = await fetch("/api/palm/sessions", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("generic_error"));
      const url = `${window.location.origin}${data.path}`;
      setPalmLink(url);
      setCopied(await copyText(url) ? true : null);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-4 py-12">
      <header className="mb-8 text-center">
        <h1 className="heading-display text-4xl">{t("palm_title")}</h1>
        <div className="ornament mt-2 text-xs">✦</div>
        <p className="mt-3 text-sm text-[var(--ink-muted)]">{t("palm_page_desc")}</p>
      </header>

      <section className="card space-y-4 p-6 text-center">
        <button onClick={mint} disabled={busy} className="btn-gold">
          {busy ? "…" : t("palm_mint_btn")}
        </button>
        {error && <p className="text-sm text-red-400">{error}</p>}

        {palmLink && (
          <div className="space-y-3 text-xs">
            <p className="text-[var(--ink-muted)]">{t("share_link")}</p>
            <code className="block break-all rounded-lg border border-[var(--line-soft)] bg-[var(--surface-deep)] p-3 text-[var(--gold)]">
              {palmLink}
            </code>
            <div className="flex flex-wrap justify-center gap-2">
              <button onClick={async () => setCopied(await copyText(palmLink))}
                      className="btn-gold px-4 py-1.5 text-xs">
                {copied ? t("copied") : t("copy")}
              </button>
              <a href={`https://wa.me/?text=${encodeURIComponent(`${t("palm_share_msg")} ${palmLink}`)}`}
                 target="_blank" rel="noopener noreferrer"
                 className="rounded-lg border border-[#25D366] px-4 py-1.5 text-[#25D366] transition-colors hover:bg-[#25D366]/10">
                {t("share_whatsapp")}
              </a>
              {typeof navigator !== "undefined" && "share" in navigator && (
                <button onClick={() => navigator.share({ text: t("palm_share_msg"), url: palmLink }).catch(() => {})}
                        className="btn-ghost px-4 py-1.5 text-xs">
                  {t("share_native")}
                </button>
              )}
            </div>
            {copied === false && <p className="text-orange-300">{t("copy_failed")}</p>}
          </div>
        )}
      </section>

      <footer className="mt-10 text-center text-xs text-[var(--ink-muted)]">{t("disclaimer")}</footer>
    </main>
  );
}
