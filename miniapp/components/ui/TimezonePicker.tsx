"use client";

import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Check, ChevronDown, Search } from "lucide-react";
import { hapticSelection } from "@/lib/telegram";
import { inputClass } from "@/components/ui";

// Common search aliases → IANA zone ids. When the query matches a key, we
// surface that zone at the top of the results so e.g. "bali" finds Makassar.
const ALIASES: Record<string, string> = {
  bali: "Asia/Makassar",
  moscow: "Europe/Moscow",
  kyiv: "Europe/Kyiv",
  kiev: "Europe/Kyiv",
  "new york": "America/New_York",
};

// Curated fallback used when Intl.supportedValuesOf isn't available.
const FALLBACK_ZONES: string[] = [
  "UTC",
  "Pacific/Honolulu",
  "America/Anchorage",
  "America/Los_Angeles",
  "America/Denver",
  "America/Chicago",
  "America/New_York",
  "America/Mexico_City",
  "America/Bogota",
  "America/Sao_Paulo",
  "America/Argentina/Buenos_Aires",
  "Atlantic/Reykjavik",
  "Europe/London",
  "Europe/Madrid",
  "Europe/Paris",
  "Europe/Berlin",
  "Europe/Rome",
  "Europe/Athens",
  "Europe/Kyiv",
  "Europe/Moscow",
  "Africa/Lagos",
  "Africa/Cairo",
  "Africa/Johannesburg",
  "Asia/Istanbul",
  "Asia/Dubai",
  "Asia/Karachi",
  "Asia/Kolkata",
  "Asia/Dhaka",
  "Asia/Bangkok",
  "Asia/Makassar",
  "Asia/Shanghai",
  "Asia/Singapore",
  "Asia/Tokyo",
  "Asia/Seoul",
  "Australia/Sydney",
  "Pacific/Auckland",
];

const MAX_RENDERED = 50;

/** "Asia/Makassar" → "Asia / Makassar" friendly label (underscores → spaces). */
function humanize(zone: string): string {
  return zone.replace(/_/g, " ");
}

/** Returns e.g. "UTC+8" for a zone, or "" if it can't be computed. */
function offsetLabel(zone: string): string {
  try {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: zone,
      timeZoneName: "shortOffset",
    }).formatToParts(new Date());
    const tzName = parts.find((p) => p.type === "timeZoneName")?.value ?? "";
    // tzName is like "GMT+8", "GMT-5:30" or "GMT" → normalize to "UTC…".
    const m = tzName.match(/GMT([+-]\d{1,2}(?::\d{2})?)?/);
    if (!m) return "";
    return m[1] ? `UTC${m[1]}` : "UTC+0";
  } catch {
    return "";
  }
}

/** The full IANA list when supported, else the curated fallback. */
function allZones(): string[] {
  try {
    const supported = Intl.supportedValuesOf?.("timeZone");
    if (supported && supported.length) return supported;
  } catch {
    // ignore — fall through to curated list
  }
  return FALLBACK_ZONES;
}

interface TimezonePickerProps {
  value: string;
  onChange: (zone: string) => void;
  className?: string;
}

export function TimezonePicker({
  value,
  onChange,
  className = "",
}: TimezonePickerProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listId = useId();

  // Build the candidate list once: full IANA (or fallback), always including
  // the current value even if it's somehow not in the list.
  const zones = useMemo(() => {
    const list = allZones();
    return list.includes(value) ? list : [value, ...list];
  }, [value]);

  // Precompute offsets so we don't recompute on every keystroke.
  const offsets = useMemo(() => {
    const map: Record<string, string> = {};
    for (const z of zones) map[z] = offsetLabel(z);
    return map;
  }, [zones]);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return zones.slice(0, MAX_RENDERED);

    const aliasZone = ALIASES[q];
    const matches = zones.filter((z) => {
      const hay = `${z} ${humanize(z)}`.toLowerCase();
      return hay.includes(q);
    });

    // Surface an alias-matched zone at the very top (de-duped).
    if (aliasZone) {
      const rest = matches.filter((z) => z !== aliasZone);
      return [aliasZone, ...rest].slice(0, MAX_RENDERED);
    }
    return matches.slice(0, MAX_RENDERED);
  }, [query, zones]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    // Focus the search field when the popover opens.
    inputRef.current?.focus();
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  function select(zone: string) {
    hapticSelection();
    onChange(zone);
    setOpen(false);
    setQuery("");
  }

  const currentOffset = offsets[value] ?? offsetLabel(value);
  const currentLabel = currentOffset
    ? `${humanize(value)} (${currentOffset})`
    : humanize(value);

  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => {
          hapticSelection();
          setOpen((o) => !o);
        }}
        className={`${inputClass} flex items-center justify-between gap-2 text-left ${
          open ? "border-primary shadow-ring" : ""
        }`}
      >
        <span className="truncate text-text">{currentLabel}</span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted transition ${open ? "rotate-180" : ""}`}
          aria-hidden
        />
      </button>

      {open && (
        <div className="animate-sheet-up absolute z-30 mt-2 w-full rounded-2xl border border-border bg-surface p-1.5 shadow-card">
          <div className="relative mb-1.5">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted"
              aria-hidden
            />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search city or zone…"
              aria-label="Search timezone"
              className={`${inputClass} pl-9`}
            />
          </div>
          <ul
            id={listId}
            role="listbox"
            className="max-h-60 overflow-auto"
          >
            {results.length === 0 ? (
              <li className="px-3 py-2.5 text-sm text-muted">No matches.</li>
            ) : (
              results.map((zone) => {
                const active = zone === value;
                const off = offsets[zone] ?? offsetLabel(zone);
                return (
                  <li key={zone} role="option" aria-selected={active}>
                    <button
                      type="button"
                      onClick={() => select(zone)}
                      className={`flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2.5 text-left text-sm transition ${
                        active
                          ? "bg-primary/10 text-primary"
                          : "text-text active:bg-surface-2"
                      }`}
                    >
                      <span className="min-w-0 truncate font-medium">
                        {humanize(zone)}
                        {off && (
                          <span className="ml-1 text-xs font-normal text-muted">
                            ({off})
                          </span>
                        )}
                      </span>
                      {active && <Check className="h-4 w-4 shrink-0" aria-hidden />}
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
