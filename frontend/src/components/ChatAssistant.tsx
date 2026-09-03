"use client";

/** "Ask about this jaathakam" — chat grounded in the computed chart.
 *  Unlimited for Plus / Lifetime Plus; other signed-in users spend 1 credit
 *  per question (earned by sharing); everyone else sees the two paths. */

import { useRef, useState } from "react";
import { chatUnlimited, useAccount } from "@/lib/account";
import { useLang } from "@/lib/i18n";
import type { ChartV1 } from "@/lib/types";

interface Msg { role: "user" | "assistant"; text: string }

export default function ChatAssistant({ chart }: { chart: ChartV1 }) {
  const { lang, t } = useLang();
  const { account, signedIn, refresh, sb } = useAccount();
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const endRef = useRef<HTMLDivElement>(null);

  const unlimited = chatUnlimited(account);
  const credits = account?.credits ?? 0;
  const canAsk = unlimited || credits > 0;

  const SUGGESTIONS: [string, string][] = [
    ["chat_q_marriage", t("chat_q_marriage")],
    ["chat_q_career", t("chat_q_career")],
    ["chat_q_children", t("chat_q_children")],
    ["chat_q_summary", t("chat_q_summary")],
  ];

  async function ask(question: string) {
    if (!question.trim() || busy || !canAsk) return;
    setBusy(true); setError("");
    const newMsgs: Msg[] = [...msgs, { role: "user", text: question }];
    setMsgs(newMsgs);
    setInput("");
    try {
      const res = await fetch("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chart, question, language: lang,
                               history: msgs.slice(-6) }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("generic_error"));
      setMsgs([...newMsgs, { role: "assistant", text: data.answer }]);
      if (!unlimited && sb) {
        sb.rpc("spend_credit").then(() => refresh(), () => {});
      }
      setTimeout(() => endRef.current?.scrollIntoView({ behavior: "smooth" }), 60);
    } catch (e) {
      setError(e instanceof Error ? e.message : t("generic_error"));
      setMsgs(msgs);
    } finally {
      setBusy(false);
    }
  }

  if (signedIn === false) {
    return (
      <div className="card p-6 text-center text-sm text-[var(--ink-soft)]">
        {t("chat_signin")}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[var(--ink-muted)]">{t("chat_grounded_note")}</span>
        <span className={unlimited ? "text-[var(--gold)]" : "text-[var(--ink-soft)]"}>
          {unlimited ? `✦ ${t("chat_unlimited")}` : `◈ ${credits} ${t("chat_credits")}`}
        </span>
      </div>

      {msgs.length === 0 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map(([k, q]) => (
            <button key={k} onClick={() => ask(q)} disabled={!canAsk || busy}
                    className="btn-ghost px-3 py-1.5 text-xs disabled:opacity-40">
              {q}
            </button>
          ))}
        </div>
      )}

      {msgs.length > 0 && (
        <div className="card max-h-[26rem] space-y-3 overflow-y-auto p-4">
          {msgs.map((m, i) => (
            <div key={i} className={m.role === "user" ? "text-right" : ""}>
              <div className={`inline-block max-w-[85%] whitespace-pre-wrap rounded-xl px-3.5 py-2 text-left text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-[var(--gold)]/15 text-[var(--ink)]"
                  : "bg-[var(--surface-raised)] text-[var(--ink-soft)]"}`}>
                {m.text}
              </div>
            </div>
          ))}
          {busy && <p className="text-xs text-[var(--ink-muted)]">{t("chat_thinking")}</p>}
          <div ref={endRef} />
        </div>
      )}

      {canAsk ? (
        <form className="flex gap-2"
              onSubmit={(e) => { e.preventDefault(); ask(input); }}>
          <input value={input} onChange={(e) => setInput(e.target.value)}
                 placeholder={t("chat_ph")} maxLength={500}
                 className="input flex-1 text-sm" />
          <button type="submit" disabled={busy || !input.trim()} className="btn-gold px-4 text-sm">
            {busy ? "…" : t("chat_ask")}
          </button>
        </form>
      ) : (
        <div className="card space-y-2 p-4 text-center text-sm">
          <p className="text-[var(--ink-soft)]">{t("chat_locked")}</p>
          <div className="flex flex-wrap justify-center gap-2 text-xs">
            <a href="/subscription" className="btn-gold px-4 py-1.5">✦ {t("chat_upgrade")}</a>
            <a href="/subscription#account" className="btn-ghost px-4 py-1.5">◈ {t("chat_earn")}</a>
          </div>
        </div>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}
    </div>
  );
}
