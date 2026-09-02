"use client";

/** Shareable palm-reading page. The link owner sends this URL; the recipient
 *  opens it on their phone, photographs their palm, and receives the reading.
 *  Images are analyzed in memory and never stored — only the derived reading. */

import { use, useEffect, useState } from "react";

interface Session {
  token: string; status: string; expires_at: number;
  result: null | {
    usable: boolean; reason?: string; retake_hint?: string;
    reading?: string; language?: string;
  };
}

export default function PalmPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = use(params);
  const [session, setSession] = useState<Session | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [language, setLanguage] = useState("en");
  const [consent, setConsent] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`/api/palm/sessions/${token}`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setSession)
      .catch(() => setNotFound(true));
  }, [token]);

  function onPick(list: FileList | null) {
    if (!list) return;
    const picked = Array.from(list).slice(0, 2);
    setFiles(picked);
    setPreviews(picked.map((f) => URL.createObjectURL(f)));
  }

  async function upload() {
    if (!files.length || !consent) return;
    setUploading(true); setError("");
    try {
      const form = new FormData();
      files.forEach((f, i) => form.append(`photo${i + 1}`, f));
      const res = await fetch(`/api/palm/sessions/${token}/upload?language=${language}`, {
        method: "POST", body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setSession(data);
      setFiles([]); setPreviews([]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setUploading(false);
    }
  }

  if (notFound) {
    return (
      <main className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-[#c9a227]">Link expired</h1>
        <p className="mt-2 text-sm text-[#9c8f6f]">
          This palm-reading link is no longer valid. Ask for a fresh link.
        </p>
      </main>
    );
  }
  if (!session) {
    return <main className="py-16 text-center text-[#9c8f6f]">Loading…</main>;
  }

  const result = session.result;

  return (
    <main className="mx-auto max-w-md px-4 py-8">
      <header className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-[#c9a227]">Palm Reading</h1>
        <p className="mt-1 text-xs text-[#9c8f6f]">
          Photograph your palm — the reading appears right here.
        </p>
      </header>

      {session.status === "complete" && result?.reading ? (
        <section className="space-y-4">
          <div className="whitespace-pre-wrap rounded-xl border border-[#3d2f5c] bg-[#1a1030]/60 p-5 text-sm leading-relaxed">
            {result.reading}
          </div>
          <p className="text-center text-xs text-[#9c8f6f]">
            Your photo was analyzed in memory and was not stored.
          </p>
        </section>
      ) : (
        <section className="space-y-4">
          {result && !result.usable && (
            <div className="rounded-lg border border-orange-500/40 bg-orange-500/10 p-3 text-sm text-orange-200">
              <b>Please retake:</b> {result.reason}
              <div className="mt-1 text-xs">{result.retake_hint}</div>
            </div>
          )}

          <div className="rounded-xl border border-dashed border-[#3d2f5c] p-5 text-center">
            <p className="mb-3 text-sm text-[#cbbfa4]">
              Open your palm flat, fill the frame, use bright even light.
              Dominant hand first; add the other hand as a second photo if you like.
            </p>
            <input
              id="palm-input" type="file" accept="image/*" capture="environment" multiple
              onChange={(e) => onPick(e.target.files)} className="hidden"
            />
            <label htmlFor="palm-input"
                   className="inline-block cursor-pointer rounded-lg bg-[#c9a227] px-5 py-2 font-semibold text-[#140b26]">
              {files.length ? "Change photo(s)" : "📷 Take / choose photo"}
            </label>
            {previews.length > 0 && (
              <div className="mt-4 flex justify-center gap-2">
                {previews.map((src) => (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img key={src} src={src} alt="palm preview"
                       className="h-40 rounded-lg border border-[#3d2f5c] object-cover" />
                ))}
              </div>
            )}
          </div>

          <label className="block text-sm">
            <span className="text-[#9c8f6f]">Reading language</span>
            <select value={language} onChange={(e) => setLanguage(e.target.value)}
                    className="mt-1 w-full rounded-lg border border-[#3d2f5c] bg-[#140b26] px-3 py-2">
              <option value="en">English</option>
              <option value="te">తెలుగు</option>
              <option value="hi">हिन्दी</option>
            </select>
          </label>

          <label className="flex items-start gap-2 text-xs text-[#9c8f6f]">
            <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)}
                   className="mt-0.5" />
            <span>
              I consent to my palm photo being analyzed. The photo is processed in
              memory and <b>not stored</b>; only the written reading is kept, and this
              link expires within 48 hours.
            </span>
          </label>

          <button onClick={upload} disabled={!files.length || !consent || uploading}
                  className="w-full rounded-lg bg-[#c9a227] px-5 py-3 font-semibold text-[#140b26] disabled:opacity-40">
            {uploading ? "Reading your palm…" : "Get my reading"}
          </button>
          {error && <p className="text-sm text-red-400">{error}</p>}
        </section>
      )}

      <footer className="mt-10 text-center text-xs text-[#9c8f6f]">
        For guidance and reflection — not a substitute for professional advice.
      </footer>
    </main>
  );
}
