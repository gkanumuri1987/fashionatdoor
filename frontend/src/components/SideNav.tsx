"use client";

/** Left navigation rail — desktop fixed sidebar, mobile top bar + drawer.
 *  Brand on top, nav items with active state, language + auth at the bottom. */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import AuthBar from "@/components/AuthBar";
import { LangSwitcher, useLang } from "@/lib/i18n";

const ITEMS: { href: string; key: string; icon: string }[] = [
  { href: "/", key: "nav_about", icon: "🏠" },
  { href: "/kundli", key: "nav_kundli", icon: "✧" },
  { href: "/match", key: "nav_milan", icon: "❋" },
  { href: "/vastu", key: "nav_vastu", icon: "⌂" },
  { href: "/calendar", key: "nav_calendar", icon: "🗓" },
  { href: "/palmistry", key: "nav_palm", icon: "✋" },
  { href: "/subscription", key: "nav_subscription", icon: "✦" },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { t } = useLang();
  return (
    <nav className="flex flex-col gap-1">
      {ITEMS.map((it) => {
        const active = pathname === it.href;
        return (
          <Link key={it.href} href={it.href} onClick={onNavigate}
                className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  active
                    ? "bg-[var(--gold)]/12 font-semibold text-[var(--gold)] shadow-[inset_2px_0_0_var(--gold)]"
                    : "text-[var(--ink-soft)] hover:bg-[var(--surface-raised)] hover:text-[var(--ink)]"
                }`}>
            <span className="w-5 text-center text-base" aria-hidden>{it.icon}</span>
            {t(it.key)}
          </Link>
        );
      })}
    </nav>
  );
}

export default function SideNav() {
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const palmPage = usePathname()?.startsWith("/palm/");
  if (palmPage) return null;  // recipients of a palm link get a clean page

  return (
    <>
      {/* ── Desktop rail ── */}
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 flex-col border-r border-[var(--line-soft)] bg-[var(--surface-deep)]/80 backdrop-blur-xl lg:flex">
        <Link href="/" className="px-5 pb-2 pt-6">
          <span className="heading-display text-2xl">{t("app_title")}</span>
        </Link>
        <div className="ornament mb-4 scale-75 text-[10px]">✦</div>
        <div className="flex-1 overflow-y-auto px-3">
          <NavLinks />
        </div>
        <div className="space-y-3 border-t border-[var(--line-soft)] p-4">
          <LangSwitcher />
          <AuthBar />
        </div>
      </aside>

      {/* ── Mobile top bar ── */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--line-soft)] bg-[var(--surface-deep)]/85 px-4 py-3 backdrop-blur-xl lg:hidden">
        <Link href="/" className="heading-display text-xl">{t("app_title")}</Link>
        <button onClick={() => setOpen(true)} aria-label="Open menu"
                className="rounded-lg border border-[var(--line)] px-3 py-1.5 text-[var(--ink-soft)]">
          ☰
        </button>
      </header>

      {/* ── Mobile drawer ── */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm"
               onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 flex w-72 flex-col border-r border-[var(--line-soft)] bg-[var(--surface-solid)] p-4">
            <div className="mb-4 flex items-center justify-between">
              <span className="heading-display text-xl">{t("app_title")}</span>
              <button onClick={() => setOpen(false)} aria-label="Close menu"
                      className="rounded-lg px-2 py-1 text-[var(--ink-muted)]">✕</button>
            </div>
            <div className="flex-1">
              <NavLinks onNavigate={() => setOpen(false)} />
            </div>
            <div className="space-y-3 border-t border-[var(--line-soft)] pt-4">
              <LangSwitcher />
              <AuthBar />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
