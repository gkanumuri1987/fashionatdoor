"use client";

/** Sidebar auth state: signed-in shows email (links to /profile) + sign-out;
 *  signed-out shows a Sign in button that navigates to the full /signin page
 *  (a modal in the sidebar was cramped by its layout context). */

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { supabase } from "@/lib/supabase";

export default function AuthBar() {
  const { t } = useLang();
  const sb = supabase();

  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    if (!sb) return;
    sb.auth.getUser().then(({ data }) => setUserEmail(data.user?.email ?? null));
    const { data: sub } = sb.auth.onAuthStateChange((_e, session) => {
      setUserEmail(session?.user?.email ?? null);
    });
    return () => sub.subscription.unsubscribe();
  }, [sb]);

  if (!sb) return null;

  if (userEmail) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <a href="/profile" className="truncate text-xs text-[var(--ink-muted)] hover:text-[var(--gold)]"
           title={t("nav_profile")}>
          {userEmail}
        </a>
        <button onClick={() => sb.auth.signOut()} className="btn-ghost px-3 py-1 text-xs">
          {t("sign_out")}
        </button>
      </div>
    );
  }

  return (
    <a href="/signin" className="btn-gold block w-full py-1.5 text-center text-sm">
      {t("sign_in")}
    </a>
  );
}
