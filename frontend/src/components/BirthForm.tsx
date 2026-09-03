"use client";

import { useEffect, useRef, useState } from "react";
import { useLang } from "@/lib/i18n";
import DateDMY from "@/components/DateDMY";

export interface BirthValue {
  date: string;
  time: string;
  lat: number | null;
  lng: number | null;
  placeName: string;
}

interface Place { name: string; lat: number; lng: number }

export function BirthForm({ label, value, onChange }: {
  label: string;
  value: BirthValue;
  onChange: (v: BirthValue) => void;
}) {
  const { t } = useLang();
  const [query, setQuery] = useState(value.placeName);
  const [places, setPlaces] = useState<Place[]>([]);
  const debounce = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    if (query.trim().length < 3 || query === value.placeName) {
      setPlaces([]);
      return;
    }
    clearTimeout(debounce.current);
    debounce.current = setTimeout(async () => {
      try {
        const res = await fetch(`/api/geocode?q=${encodeURIComponent(query)}`);
        if (res.ok) setPlaces(await res.json());
      } catch { /* best-effort */ }
    }, 400);
    return () => clearTimeout(debounce.current);
  }, [query, value.placeName]);

  return (
    <div className="rounded-xl border border-[var(--line)] bg-[var(--surface)] p-4">
      <h3 className="mb-3 font-semibold text-[var(--gold)]">{label}</h3>
      <div className="space-y-3 text-sm">
        <label className="block">
          <span className="text-[var(--ink-muted)]">{t("dob")}</span>
          <DateDMY value={value.date}
                   onChange={(iso) => onChange({ ...value, date: iso })} />
        </label>
        <label className="block">
          <span className="text-[var(--ink-muted)]">{t("tob")}</span>
          <input type="time" value={value.time}
                 onChange={(e) => onChange({ ...value, time: e.target.value })}
                 className="mt-1 w-full rounded-lg border border-[var(--line)] bg-[var(--surface-deep)] px-3 py-2" />
        </label>
        <label className="relative block">
          <span className="text-[var(--ink-muted)]">{t("pob")}</span>
          <input value={query}
                 onChange={(e) => { setQuery(e.target.value); onChange({ ...value, lat: null, lng: null, placeName: "" }); }}
                 placeholder={t("place_ph")}
                 className="mt-1 w-full rounded-lg border border-[var(--line)] bg-[var(--surface-deep)] px-3 py-2" />
          {places.length > 0 && (
            <ul className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-[var(--line)] bg-[var(--surface-raised)] text-xs shadow-xl">
              {places.map((p) => (
                <li key={p.name}>
                  <button type="button" className="w-full px-3 py-2 text-left hover:bg-[var(--gold)]/10"
                          onClick={() => {
                            onChange({ ...value, lat: p.lat, lng: p.lng, placeName: p.name });
                            setQuery(p.name);
                            setPlaces([]);
                          }}>
                    {p.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </label>
      </div>
    </div>
  );
}
