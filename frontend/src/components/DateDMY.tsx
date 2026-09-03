"use client";

/** DD / MM / YYYY segmented date field — Indian format, locale-independent.
 *  Native <input type="date"> renders in the BROWSER'S locale (mm/dd/yyyy on
 *  US machines), which confuses birth-date entry; three explicit segments
 *  cannot be misread. Stores/emits ISO (yyyy-mm-dd). Auto-advances between
 *  segments, numeric keyboards on mobile. */

import { useRef } from "react";

export default function DateDMY({ value, onChange }: {
  value: string;                       // ISO yyyy-mm-dd (or "")
  onChange: (iso: string) => void;
}) {
  const [y, m, d] = value ? value.split("-") : ["", "", ""];
  const mRef = useRef<HTMLInputElement>(null);
  const yRef = useRef<HTMLInputElement>(null);

  function emit(dd: string, mm: string, yyyy: string) {
    if (dd.length >= 1 && mm.length >= 1 && yyyy.length === 4) {
      const dn = Math.min(31, Math.max(1, parseInt(dd) || 1));
      const mn = Math.min(12, Math.max(1, parseInt(mm) || 1));
      onChange(`${yyyy}-${String(mn).padStart(2, "0")}-${String(dn).padStart(2, "0")}`);
    } else {
      onChange("");
    }
  }

  const seg = "input mt-1 text-center tabular-nums";
  return (
    <div className="flex items-end gap-1.5">
      <input inputMode="numeric" pattern="[0-9]*" placeholder="DD" maxLength={2}
             defaultValue={d} aria-label="Day"
             className={`${seg} w-14`}
             onChange={(e) => {
               const v = e.target.value.replace(/\D/g, "").slice(0, 2);
               e.target.value = v;
               emit(v, mRef.current?.value ?? "", yRef.current?.value ?? "");
               if (v.length === 2) mRef.current?.focus();
             }} />
      <span className="pb-2 text-[var(--ink-faint)]">/</span>
      <input ref={mRef} inputMode="numeric" pattern="[0-9]*" placeholder="MM" maxLength={2}
             defaultValue={m} aria-label="Month"
             className={`${seg} w-14`}
             onChange={(e) => {
               const v = e.target.value.replace(/\D/g, "").slice(0, 2);
               e.target.value = v;
               const dd = (e.target.parentElement?.querySelector('[aria-label="Day"]') as HTMLInputElement)?.value ?? "";
               emit(dd, v, yRef.current?.value ?? "");
               if (v.length === 2) yRef.current?.focus();
             }} />
      <span className="pb-2 text-[var(--ink-faint)]">/</span>
      <input ref={yRef} inputMode="numeric" pattern="[0-9]*" placeholder="YYYY" maxLength={4}
             defaultValue={y} aria-label="Year"
             className={`${seg} w-20`}
             onChange={(e) => {
               const v = e.target.value.replace(/\D/g, "").slice(0, 4);
               e.target.value = v;
               const root = e.target.parentElement;
               const dd = (root?.querySelector('[aria-label="Day"]') as HTMLInputElement)?.value ?? "";
               const mm = (root?.querySelector('[aria-label="Month"]') as HTMLInputElement)?.value ?? "";
               emit(dd, mm, v);
             }} />
    </div>
  );
}
