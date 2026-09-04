"use client";

/** Admin — owner-only. Review new user registrations and approve / reject
 *  access. Only kanumuri.choudary@gmail.com can see any data here (the RPCs are
 *  owner-gated server-side; this page also hides itself for everyone else). */

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { OWNER_EMAIL } from "@/lib/account";
import { toDDMMYYYY } from "@/lib/date";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

interface Reg {
  user_id: string;
  email: string;
  created_at: string;
  approval_status?: string;
  plan?: string;
}

const STATUS_STYLE: Record<string, string> = {
  approved: "text-[var(--good)]",
  pending: "text-[var(--warn)]",
  rejected: "text-[var(--bad)]",
};

export default function AdminPage() {
  const { t } = useLang();
  const sb = supabase();
  const [isOwner, setIsOwner] = useState<boolean | null>(null);
  const [pending, setPending] = useState<Reg[]>([]);
  const [all, setAll] = useState<Reg[]>([]);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    if (!sb) return;
    const [{ data: p }, { data: a }] = await Promise.all([
      sb.rpc("pending_signups").then((r) => r, () => ({ data: null })),
      sb.rpc("all_signups").then((r) => r, () => ({ data: null })),
    ]);
    setPending((p as Reg[]) ?? []);
    setAll((a as Reg[]) ?? []);
  }, [sb]);

  useEffect(() => {
    if (!sb) { setIsOwner(false); return; }
    sb.auth.getUser().then(({ data }) => {
      const owner = (data.user?.email ?? "").toLowerCase() === OWNER_EMAIL;
      setIsOwner(owner);
      if (owner) load();
    });
  }, [sb, load]);

  async function decide(id: string, status: string, email: string) {
    if (!sb) return;
    setBusy(id); setMsg("");
    const { data, error } = await sb.rpc("set_approval", { target: id, new_status: status });
    setBusy("");
    if (error) {
      setMsg(error.code === "42883"
        ? "Run db_migrations/009_signup_approval.sql in Supabase first."
        : error.message);
      return;
    }
    if (data === false) { setMsg("Not permitted."); return; }
    setMsg(`${email} → ${status}`);
    load();
  }

  if (isOwner === null) {
    return <main className="mx-auto max-w-3xl px-4 py-12 text-sm text-[var(--ink-muted)]">…</main>;
  }
  if (!isOwner) {
    return (
      <main className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="heading-display text-3xl">{t("admin_denied_title")}</h1>
        <p className="mt-3 text-sm text-[var(--ink-soft)]">{t("admin_denied_body")}</p>
        <Link href="/" className="btn-ghost mt-6 inline-flex">← {t("nav_about")}</Link>
      </main>
    );
  }

  const Row = ({ r, showActions }: { r: Reg; showActions: boolean }) => (
    <li className="flex flex-wrap items-center justify-between gap-2 py-2.5 text-sm">
      <div className="min-w-0">
        <div className="truncate font-medium text-[var(--ink)]">{r.email}</div>
        <div className="text-xs text-[var(--ink-muted)]">
          {t("admin_joined")} {toDDMMYYYY(r.created_at)}
          {r.approval_status && (
            <span className={`ml-2 ${STATUS_STYLE[r.approval_status] ?? ""}`}>
              · {t(`admin_status_${r.approval_status}`)}
            </span>
          )}
        </div>
      </div>
      <div className="flex shrink-0 gap-2">
        {(showActions || r.approval_status !== "approved") && (
          <button disabled={busy === r.user_id}
                  onClick={() => decide(r.user_id, "approved", r.email)}
                  className="btn-gold px-3 py-1 text-xs">✓ {t("admin_approve")}</button>
        )}
        {(showActions || r.approval_status === "approved") && (
          <button disabled={busy === r.user_id}
                  onClick={() => decide(r.user_id, "rejected", r.email)}
                  className="btn-ghost px-3 py-1 text-xs">✕ {t("admin_reject")}</button>
        )}
      </div>
    </li>
  );

  return (
    <main className="mx-auto max-w-3xl px-4 py-10">
      <header className="flex items-center justify-between">
        <h1 className="heading-display text-3xl">{t("admin_title")}</h1>
        <button onClick={load} className="text-xs text-[var(--gold)] underline">{t("admin_refresh")}</button>
      </header>
      <p className="mt-2 text-sm text-[var(--ink-soft)]">{t("admin_intro")}</p>
      {msg && <p className="mt-3 rounded-lg border border-[var(--line-gold)] bg-[var(--gold)]/8 px-3 py-2 text-xs text-[var(--gold)]">{msg}</p>}

      <section className="card mt-6 p-5">
        <h2 className="heading-section text-lg text-[var(--warn)]">
          {t("admin_pending")} {pending.length > 0 && <span className="ml-1 rounded-full bg-[var(--warn)]/20 px-2 py-0.5 text-xs">{pending.length}</span>}
        </h2>
        {pending.length === 0 ? (
          <p className="mt-2 text-sm text-[var(--ink-muted)]">{t("admin_none_pending")}</p>
        ) : (
          <ul className="mt-2 divide-y divide-[var(--line-soft)]">
            {pending.map((r) => <Row key={r.user_id} r={{ ...r, approval_status: "pending" }} showActions />)}
          </ul>
        )}
      </section>

      <section className="card mt-4 p-5">
        <h2 className="heading-section text-lg">{t("admin_all")}</h2>
        {all.length === 0 ? (
          <p className="mt-2 text-sm text-[var(--ink-muted)]">—</p>
        ) : (
          <ul className="mt-2 divide-y divide-[var(--line-soft)]">
            {all.map((r) => <Row key={r.user_id} r={r} showActions={false} />)}
          </ul>
        )}
      </section>
    </main>
  );
}
