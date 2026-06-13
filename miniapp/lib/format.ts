// Small pure formatting helpers shared across components.

/** Returns a short relative-time string like "3m", "2h", "5d" or "just now". */
export function relativeTime(iso: string, now: Date = new Date()): string {
  const then = new Date(iso);
  const ms = now.getTime() - then.getTime();
  if (Number.isNaN(ms)) return "";

  const sec = Math.floor(ms / 1000);
  if (sec < 45) return "just now";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const day = Math.floor(hr / 24);
  if (day < 7) return `${day}d ago`;
  const wk = Math.floor(day / 7);
  if (wk < 5) return `${wk}w ago`;
  return then.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/** Formats an ISO date as a human date, e.g. "Jun 13, 2026". */
export function formatDate(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Formats an ISO day (YYYY-MM-DD) into a short axis label like "Jun 1". */
export function shortDay(iso: string): string {
  const d = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/**
 * Returns a day-group label for an ISO timestamp:
 * "Today", "Yesterday", or a short date like "Jun 13".
 */
export function dayLabel(iso: string, now: Date = new Date()): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";

  const startOf = (x: Date) =>
    new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
  const dayMs = 86_400_000;
  const diffDays = Math.round((startOf(now) - startOf(d)) / dayMs);

  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";

  const sameYear = d.getFullYear() === now.getFullYear();
  return d.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}

/**
 * Shortens a fully-qualified model id into a compact badge label by stripping
 * the provider prefix (e.g. "openai/") and a trailing ":free" suffix.
 */
export function shortModel(model: string): string {
  const noPrefix = model.includes("/") ? model.split("/").pop()! : model;
  return noPrefix.replace(/:free$/i, "");
}

/** Truncates text to maxLen graphemes-ish, appending an ellipsis. */
export function truncate(text: string, maxLen = 80): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= maxLen) return clean;
  return `${clean.slice(0, maxLen - 1).trimEnd()}…`;
}

/** Compact number formatting: 1234 -> "1,234". */
export function formatNumber(n: number): string {
  return n.toLocaleString();
}
