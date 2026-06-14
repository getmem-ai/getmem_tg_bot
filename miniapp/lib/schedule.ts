// Pure, display-only helpers for the Schedules feature. These reason about the
// browser's *local* calendar days for labels/markers — they are not the source
// of truth for firing (the backend's `next_run_at` is). No DST math here.

import type { ScheduledTask } from "./types";

// Weekday labels — index 0 = Monday … 6 = Sunday (matches the contract).
export const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

/** Maps a JS Date.getDay() (0=Sun…6=Sat) to the contract's Mon-0 index. */
function mondayIndex(d: Date): number {
  return (d.getDay() + 6) % 7;
}

/** Truncates a Date to local midnight (a stable calendar-day key). */
function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

/** Whole-day difference (b - a) on the local calendar. */
function dayDiff(a: Date, b: Date): number {
  const ms = startOfDay(b).getTime() - startOfDay(a).getTime();
  return Math.round(ms / 86_400_000);
}

/** Parses "HH:MM" into {hour, minute}, defensively clamped. */
export function parseHHMM(hhmm: string): { hour: number; minute: number } {
  const [rawH = "0", rawM = "0"] = (hhmm || "").split(":");
  const hour = Math.min(23, Math.max(0, parseInt(rawH, 10) || 0));
  const minute = Math.min(59, Math.max(0, parseInt(rawM, 10) || 0));
  return { hour, minute };
}

/** Human label for a task's frequency, e.g. "Every day" or "Mon, Wed, Fri". */
export function frequencyLabel(task: ScheduledTask): string {
  switch (task.frequency) {
    case "daily":
      return "Every day";
    case "weekly": {
      const days = [...task.weekdays]
        .sort((a, b) => a - b)
        .map((d) => WEEKDAY_LABELS[d])
        .filter(Boolean);
      return days.length ? days.join(", ") : "Specific days";
    }
    case "interval": {
      const n = task.interval_days ?? 1;
      return n === 1 ? "Every day" : `Every ${n} days`;
    }
    case "as_needed":
      return "As needed";
    default:
      return "Schedule";
  }
}

/** "08:00" → "8:00 AM" (12-hour label). */
export function timeChip(hhmm: string): string {
  const { hour, minute } = parseHHMM(hhmm);
  const period = hour < 12 ? "AM" : "PM";
  const h12 = hour % 12 === 0 ? 12 : hour % 12;
  return `${h12}:${String(minute).padStart(2, "0")} ${period}`;
}

/** Maps "HH:MM"[] to 12-hour chip labels. */
export function timeChips(times: string[]): string[] {
  return times.map(timeChip);
}

/**
 * How many times a task runs on a given local calendar day. Used for calendar
 * markers. as_needed never fires; interval is counted from created_at's date.
 */
export function occursOnDay(task: ScheduledTask, day: Date): number {
  if (task.frequency === "as_needed") return 0;
  const count = task.times.length;
  if (count === 0) return 0;

  if (task.frequency === "daily") return count;

  if (task.frequency === "weekly") {
    return task.weekdays.includes(mondayIndex(day)) ? count : 0;
  }

  if (task.frequency === "interval") {
    const n = task.interval_days ?? 0;
    if (n < 1) return 0;
    const anchor = new Date(task.created_at);
    if (Number.isNaN(anchor.getTime())) return 0;
    const diff = dayDiff(anchor, day);
    if (diff < 0) return 0;
    return diff % n === 0 ? count : 0;
  }

  return 0;
}

export interface Occurrence {
  task: ScheduledTask;
  when: Date;
}

/**
 * Upcoming runs across enabled tasks, scanning ~`scanDays` forward. Each task's
 * times are applied to its valid days, filtered to strictly-future moments,
 * sorted ascending and capped to `count`.
 */
export function nextOccurrences(
  tasks: ScheduledTask[],
  count: number,
  now: Date = new Date(),
  scanDays = 60,
): Occurrence[] {
  const out: Occurrence[] = [];
  const active = tasks.filter((t) => t.enabled && t.frequency !== "as_needed");
  if (active.length === 0) return out;

  const base = startOfDay(now);
  for (let i = 0; i <= scanDays; i++) {
    const day = new Date(base.getFullYear(), base.getMonth(), base.getDate() + i);
    for (const task of active) {
      if (occursOnDay(task, day) === 0) continue;
      for (const t of task.times) {
        const { hour, minute } = parseHHMM(t);
        const when = new Date(
          day.getFullYear(),
          day.getMonth(),
          day.getDate(),
          hour,
          minute,
          0,
          0,
        );
        if (when.getTime() > now.getTime()) out.push({ task, when });
      }
    }
  }

  out.sort((a, b) => a.when.getTime() - b.when.getTime());
  return out.slice(0, count);
}

/** "Today" | "Tomorrow" | "Mon 16 Jun" for a local Date. */
export function dayLabel(d: Date, now: Date = new Date()): string {
  const diff = dayDiff(now, d);
  if (diff === 0) return "Today";
  if (diff === 1) return "Tomorrow";
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export type TimeOfDayKey = "morning" | "noon" | "evening" | "night";

/** Buckets an "HH:MM" into a time-of-day segment for icons/labels. */
export function timeOfDay(hhmm: string): { key: TimeOfDayKey; label: string } {
  const { hour } = parseHHMM(hhmm);
  if (hour >= 5 && hour < 11) return { key: "morning", label: "Morning" };
  if (hour >= 11 && hour < 16) return { key: "noon", label: "Noon" };
  if (hour >= 16 && hour < 21) return { key: "evening", label: "Evening" };
  return { key: "night", label: "Night" };
}
