"use client";

/** Shareable palm-reading page. The link owner sends this URL; the recipient
 *  opens it on their phone, photographs their palm, and receives the reading.
 *  Images are analyzed in memory and never stored — only the derived reading. */

import { use, useEffect, useState } from "react";
import { useLang, LANG_LABELS, type Lang } from "@/lib/i18n";
import { compressImage } from "@/lib/image";

interface Session {
  token: string; status: string; expires_at: number;
  result: null | {
    usable: boolean; reason?: string; retake_hint?: string;
    reading?: string; language?: string;
  };
}

export default function PalmPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const { lang, setLang, t } = useLang();
  const [session, setSession] = useState<Session | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [consent, setConsent] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`/api/palm/sessions/${token}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setSession)
      .catch(() => setNotFound(true));
  }, [token]);

  async function onPick(list: FileList | null) {
    if (!list) return;
    const picked = await Promise.all(
      Array.from(list).slice(0, 2).map((f) => compressImage(f)));
    setFiles(picked);
    setPreviews(picked.map((f) => URL.createObjectURL(f)));
  }

  async function upload() {
    if (!files.length || !consent) return;
    setUploading(true); setError("");
    try {
      const form = new FormData();
      files.forEach((f, i) => form.append(`photo${i + 1}`, f));
      const res = await fetch(`/api/palm/sessions/${token}/upload?language=${lang}`, {
        method: "POST", body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("generic_error"));
      setSession(data);
      setFiles([]); setPreviews([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
    } finally {
      setUploading(false);
    }
  }

  if (notFound) {
    return (
      <main className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="heading-display text-3xl">{t("link_expired")}</h1>
        <p className="mt-2 text-sm text-[var(--ink-muted)]">{t("link_expired_sub")}</p>
      </main>
    );
  }
  if (!session) {
    return <main className="py-16 text-center text-[var(--ink-muted)]">{t("loading")}</main>;
  }

  const result = session.result;

  return (
    <main className="mx-auto max-w-md px-4 py-8">
      <header className="mb-6 text-center">
        <h1 className="heading-display text-3xl">{t("palm_title")}</h1>
        <p className="mt-1 text-xs text-[var(--ink-muted)]">{t("palm_sub")}</p>
      </header>

      {session.status === "complete" && result?.reading ? (
        <section className="space-y-4">
          <div className="card whitespace-pre-wrap p-5 text-sm leading-relaxed">
            {result.reading}
          </div>
          <p className="text-center text-xs text-[var(--ink-muted)]">{t("photo_not_stored")}</p>
        </section>
      ) : (
        <section className="space-y-4">
          {result && !result.usable && (
            <div className="rounded-lg border border-orange-500/40 bg-orange-500/10 p-3 text-sm text-orange-200">
              <b>{t("retake")}</b> {result.reason}
              <div className="mt-1 text-xs">{result.retake_hint}</div>
            </div>
          )}

          <div className="rounded-xl border border-dashed border-[var(--line)] p-5 text-center">
            <p className="mb-3 text-sm text-[var(--ink-soft)]">{t("palm_instructions")}</p>
            <input
              id="palm-input" type="file" accept="image/*" capture="environment" multiple
              onChange={(e) => onPick(e.target.files)} className="hidden"
            />
            <label htmlFor="palm-input"
                   className="btn-gold cursor-pointer">
              {files.length ? t("change_photos") : t("take_photo")}
            </label>
            {previews.length > 0 && (
              <div className="mt-4 flex justify-center gap-2">
                {previews.map((src) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={src} src={src} alt="palm preview"
                       className="h-40 rounded-lg border border-[var(--line)] object-cover" />
                ))}
              </div>
            )}
          </div>

          <label className="block text-sm">
            <span className="text-[var(--ink-muted)]">{t("reading_language")}</span>
            <select value={lang} onChange={(e) => setLang(e.target.value as Lang)}
                    className="input mt-1">
              {(Object.keys(LANG_LABELS) as Lang[]).map((l) => (
                <option key={l} value={l}>{LANG_LABELS[l]}</option>
              ))}
            </select>
          </label>

          <label className="flex items-start gap-2 text-xs text-[var(--ink-muted)]">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
                   className="mt-0.5" />
            <span>{t("consent_text")}</span>
          </label>

          <button onClick={upload} disabled={!files.length || !consent || uploading}
                  className="btn-gold w-full py-3">
            {uploading ? t("reading_palm") : t("get_reading")}
          </button>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </section>
      )}

      <footer className="mt-10 text-center text-xs text-[var(--ink-muted)]">{t("disclaimer")}</footer>
    </main>
  );
}
