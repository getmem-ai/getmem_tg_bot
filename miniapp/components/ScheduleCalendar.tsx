"use client";

import { useMemo, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { ScheduledTask } from "@/lib/types";
import { occursOnDay } from "@/lib/schedule";
import { hapticSelection } from "@/lib/telegram";

const WEEKDAY_HEADERS = ["M", "T", "W", "T", "F", "S", "S"];

interface DayCell {
  date: Date;
  inMonth: boolean;
  runs: number;
}

/** Same local calendar day? */
function sameDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

interface ScheduleCalendarProps {
  tasks: ScheduledTask[];
  selected: Date | null;
  onSelect: (day: Date) => void;
}

export function ScheduleCalendar({ tasks, selected, onSelect }: ScheduleCalendarProps) {
  const today = useMemo(() => new Date(), []);
  // The first day of the month currently shown.
  const [cursor, setCursor] = useState(
    () => new Date(today.getFullYear(), today.getMonth(), 1),
  );

  const active = useMemo(
    () => tasks.filter((t) => t.enabled && t.frequency !== "as_needed"),
    [tasks],
  );

  const cells = useMemo<DayCell[]>(() => {
    const year = cursor.getFullYear();
    const month = cursor.getMonth();
    const first = new Date(year, month, 1);
    // Mon-first offset: JS getDay() 0=Sun…6=Sat → 0=Mon…6=Sun.
    const lead = (first.getDay() + 6) % 7;
    const start = new Date(year, month, 1 - lead);

    return Array.from({ length: 42 }, (_, i) => {
      const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
      const runs = active.reduce((sum, t) => sum + occursOnDay(t, date), 0);
      return { date, inMonth: date.getMonth() === month, runs };
    });
  }, [cursor, active]);

  // Trim trailing all-out-of-month week (keep grid tight when it fits in 5 rows).
  const visibleCells = useMemo(() => {
    const lastWeek = cells.slice(35);
    return lastWeek.every((c) => !c.inMonth) ? cells.slice(0, 35) : cells;
  }, [cells]);

  const monthTitle = cursor.toLocaleDateString(undefined, {
    month: "long",
    year: "numeric",
  });

  function shiftMonth(delta: number) {
    hapticSelection();
    setCursor((c) => new Date(c.getFullYear(), c.getMonth() + delta, 1));
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <button
          type="button"
          onClick={() => shiftMonth(-1)}
          aria-label="Previous month"
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted transition active:bg-surface-2"
        >
          <ChevronLeft className="h-5 w-5" aria-hidden />
        </button>
        <p className="text-sm font-bold text-text">{monthTitle}</p>
        <button
          type="button"
          onClick={() => shiftMonth(1)}
          aria-label="Next month"
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted transition active:bg-surface-2"
        >
          <ChevronRight className="h-5 w-5" aria-hidden />
        </button>
      </div>

      <div className="mb-1 grid grid-cols-7 gap-1">
        {WEEKDAY_HEADERS.map((d, i) => (
          <span
            key={i}
            className="py-1 text-center text-[10px] font-semibold uppercase text-muted"
          >
            {d}
          </span>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-1">
        {visibleCells.map((cell, i) => {
          const isToday = sameDay(cell.date, today);
          const isSelected = selected != null && sameDay(cell.date, selected);
          const marked = cell.runs > 0 && cell.inMonth;
          const strong = cell.runs >= 3;

          // Fill: solid blue circle (white number) for 3+, a clearly tinted
          // circle for 1–2, nothing otherwise.
          let fill = "";
          if (strong) fill = "bg-primary text-white shadow-soft";
          else if (marked) fill = "bg-primary/20 text-text";
          else if (cell.inMonth) fill = "text-text";
          else fill = "text-muted/40";

          return (
            <button
              key={i}
              type="button"
              disabled={!cell.inMonth}
              onClick={() => {
                if (!marked) return;
                hapticSelection();
                onSelect(cell.date);
              }}
              aria-label={`${cell.date.toLocaleDateString()}${
                marked ? `, ${cell.runs} reminder${cell.runs > 1 ? "s" : ""}` : ""
              }`}
              aria-pressed={isSelected}
              className={`relative flex aspect-square flex-col items-center justify-center gap-0.5 rounded-full text-xs font-semibold transition ${
                isSelected
                  ? "ring-2 ring-primary ring-offset-1 ring-offset-surface"
                  : isToday
                    ? "ring-1 ring-primary/60"
                    : ""
              } ${fill} ${marked ? "active:scale-[0.95]" : "cursor-default"}`}
            >
              <span className="leading-none">{cell.date.getDate()}</span>
              {/* A solid dot under the number for 1–2 days (3+ already filled). */}
              <span
                aria-hidden
                className={`h-1 w-1 rounded-full ${
                  marked && !strong ? "bg-primary" : "bg-transparent"
                }`}
              />
            </button>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-3 flex items-center justify-center gap-4 text-[11px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-3.5 w-3.5 rounded-full bg-primary/20" aria-hidden />
          1–2 reminders
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-3.5 w-3.5 rounded-full bg-primary" aria-hidden />
          3+ reminders
        </span>
      </div>
    </div>
  );
}
