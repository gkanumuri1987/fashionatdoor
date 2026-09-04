"use client";

/** Left navigation rail — desktop fixed sidebar, mobile top bar + drawer.
 *  Brand on top, nav items with active state, language + auth at the bottom. */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import AuthBar from "@/components/AuthBar";
import Icon, { type IconName } from "@/components/Icon";
import Logo from "@/components/Logo";
import { LangSwitcher, useLang } from "@/lib/i18n";

const ITEMS: { href: string; key: string; icon: IconName }[] = [
  { href: "/", key: "nav_about", icon: "about" },
  { href: "/kundli", key: "nav_kundli", icon: "chart" },
  { href: "/match", key: "nav_milan", icon: "match" },
  { href: "/vastu", key: "nav_vastu", icon: "vastu" },
  { href: "/calendar", key: "nav_calendar", icon: "calendar" },
  { href: "/palmistry", key: "nav_palm", icon: "palm" },
  { href: "/subscription", key: "nav_subscription", icon: "plans" },
  { href: "/profile", key: "nav_profile", icon: "account" },
];

function NavFooter() {
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-1 text-[11px] text-[var(--ink-faint)]">
      <Link href="/privacy" className="hover:text-[var(--ink-soft)]">Privacy</Link>
      <span aria-hidden>·</span>
      <a href="https://github.com/gkanumuri1987/fashionatdoor" target="_blank"
         rel="noopener noreferrer" className="hover:text-[var(--ink-soft)]">Source</a>
    </div>
  );
}

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
            <Icon name={it.icon} className={`h-[18px] w-[18px] shrink-0 ${active ? "text-[var(--gold)]" : "text-[var(--ink-faint)]"}`} />
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
        <Link href="/" className="px-5 pb-3 pt-6">
          <Logo size={30} />
        </Link>
        <div className="flex-1 overflow-y-auto px-3">
          <NavLinks />
        </div>
        <div className="space-y-3 border-t border-[var(--line-soft)] p-4">
          <LangSwitcher />
          <AuthBar />
          <NavFooter />
        </div>
      </aside>

      {/* ── Mobile top bar ── */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--line-soft)] bg-[var(--surface-deep)]/85 px-4 py-3 backdrop-blur-xl lg:hidden">
        <Link href="/"><Logo size={26} /></Link>
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
              <Logo size={26} />
              <button onClick={() => setOpen(false)} aria-label="Close menu"
                      className="rounded-lg px-2 py-1 text-[var(--ink-muted)]">✕</button>
            </div>
            <div className="flex-1">
              <NavLinks onNavigate={() => setOpen(false)} />
            </div>
            <div className="space-y-3 border-t border-[var(--line-soft)] pt-4">
              <LangSwitcher />
              <AuthBar />
              <NavFooter />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
