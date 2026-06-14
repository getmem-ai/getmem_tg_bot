"use client";

import {
  useEffect,
  useMemo,
  useState,
  type ComponentType,
} from "react";
import { createPortal } from "react-dom";
import {
  Calendar,
  CalendarDays,
  ChevronLeft,
  Moon,
  Repeat,
  Save,
  Sparkles,
  Sunrise,
  Sunset,
  Utensils,
  X,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { ScheduleFrequency, ScheduleInput, ScheduledTask } from "@/lib/types";
import { haptic, hapticSelection } from "@/lib/telegram";
import {
  WEEKDAY_LABELS,
  frequencyLabel,
  parseHHMM,
  timeChip,
  timeOfDay,
  type TimeOfDayKey,
} from "@/lib/schedule";
import {
  Button,
  Field,
  Input,
  SaveMessage,
  SegmentedControl,
  Select,
  Toggle,
  type SaveStatus,
  type SelectOption,
} from "./ui";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

type WizardFrequency = "daily" | "weekly" | "interval" | "as_needed";

const textareaClass =
  "w-full resize-y rounded-2xl border border-border bg-surface-2/60 p-3 text-sm text-text outline-none transition placeholder:text-muted focus:border-primary focus:bg-surface focus:shadow-ring";

// Hour (00–23) and minute (00,05,…,55) options for the time picker.
const HOUR_OPTIONS: SelectOption<string>[] = Array.from({ length: 24 }, (_, h) => {
  const v = String(h).padStart(2, "0");
  return { value: v, label: v };
});

const MINUTE_OPTIONS: SelectOption<string>[] = Array.from({ length: 12 }, (_, i) => {
  const v = String(i * 5).padStart(2, "0");
  return { value: v, label: v };
});

/** Snap an "HH:MM" to padded hour + nearest-5 minute. */
function splitTime(value: string): { hour: string; minute: string } {
  const { hour, minute } = parseHHMM(value || "09:00");
  const m = Math.min(55, Math.round(minute / 5) * 5);
  return {
    hour: String(hour).padStart(2, "0"),
    minute: String(m).padStart(2, "0"),
  };
}

// Default times seeded when the "times per day" count changes.
const DEFAULT_TIMES: Record<number, string[]> = {
  1: ["09:00"],
  2: ["08:00", "20:00"],
  3: ["08:00", "14:00", "20:00"],
  4: ["08:00", "13:00", "18:00", "21:00"],
};

const TIME_OF_DAY_ICON: Record<TimeOfDayKey, IconType> = {
  morning: Sunrise,
  noon: Utensils,
  evening: Sunset,
  night: Moon,
};

const FREQ_CARDS: {
  value: WizardFrequency;
  title: string;
  hint: string;
  icon: IconType;
}[] = [
  { value: "daily", title: "Every day", hint: "Runs daily", icon: Calendar },
  { value: "weekly", title: "Specific days", hint: "Pick weekdays", icon: CalendarDays },
  { value: "interval", title: "Every N days", hint: "Repeat interval", icon: Repeat },
  { value: "as_needed", title: "As needed", hint: "No fixed schedule", icon: Sparkles },
];

const COUNT_OPTIONS: { value: string; label: string }[] = [
  { value: "1", label: "1×" },
  { value: "2", label: "2×" },
  { value: "3", label: "3×" },
  { value: "4", label: "4×" },
];

interface ScheduleWizardProps {
  task?: ScheduledTask | null;
  onClose: () => void;
  onSaved: () => void;
}

/** Maps a stored frequency to a wizard frequency, defaulting to daily. */
function toWizardFrequency(f: ScheduleFrequency): WizardFrequency {
  return f === "weekly" || f === "interval" || f === "as_needed" ? f : "daily";
}

export function ScheduleWizard({ task, onClose, onSaved }: ScheduleWizardProps) {
  const [mounted, setMounted] = useState(false);
  const [step, setStep] = useState(1);

  const [title, setTitle] = useState(task?.title ?? "");
  const [prompt, setPrompt] = useState(task?.prompt ?? "");
  const [frequency, setFrequency] = useState<WizardFrequency>(
    task ? toWizardFrequency(task.frequency) : "daily",
  );
  const [weekdays, setWeekdays] = useState<number[]>(task ? [...task.weekdays] : []);
  const [intervalDays, setIntervalDays] = useState<number>(
    task?.interval_days && task.interval_days >= 1 ? task.interval_days : 2,
  );
  const [times, setTimes] = useState<string[]>(() => {
    if (task && task.frequency !== "as_needed" && task.times.length) {
      return task.times.map((t) => {
        const { hour, minute } = splitTime(t);
        return `${hour}:${minute}`;
      });
    }
    return DEFAULT_TIMES[1];
  });
  const [enabled, setEnabled] = useState(task?.enabled ?? true);

  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  // Portal to <body>; lock background scroll while open.
  useEffect(() => {
    setMounted(true);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const isAsNeeded = frequency === "as_needed";

  // For as_needed the time step is skipped → only 3 visible steps map onto the
  // progress bar, but we keep the logical numbering simple by jumping 2↔4.
  const stepsForFreq = isAsNeeded ? [1, 2, 4] : [1, 2, 3, 4];
  const visibleIndex = Math.max(0, stepsForFreq.indexOf(step));
  const visibleTotal = stepsForFreq.length;

  function setCount(n: number) {
    hapticSelection();
    setTimes(DEFAULT_TIMES[n] ?? DEFAULT_TIMES[1]);
  }

  function setTimeAt(index: number, value: string) {
    setTimes((prev) => prev.map((t, i) => (i === index ? value : t)));
  }

  function toggleWeekday(day: number) {
    hapticSelection();
    setWeekdays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day],
    );
  }

  function goNext() {
    haptic("light");
    const idx = stepsForFreq.indexOf(step);
    if (idx >= 0 && idx < stepsForFreq.length - 1) {
      setStep(stepsForFreq[idx + 1]);
    }
  }

  function goBack() {
    haptic("light");
    const idx = stepsForFreq.indexOf(step);
    if (idx > 0) {
      setStep(stepsForFreq[idx - 1]);
    }
  }

  const reviewFrequencyLabel = useMemo(
    () =>
      frequencyLabel({
        frequency,
        weekdays,
        interval_days: intervalDays,
        times,
      } as ScheduledTask),
    [frequency, weekdays, intervalDays, times],
  );

  const step1Valid = title.trim().length > 0 && prompt.trim().length > 0;
  const step2Valid =
    frequency === "weekly" ? weekdays.length > 0 : true; // interval N is clamped 1–30

  async function save() {
    setStatus("saving");
    setMessage("");
    const input: ScheduleInput = {
      title: title.trim(),
      prompt: prompt.trim(),
      frequency,
      times: isAsNeeded ? [] : times,
      weekdays: frequency === "weekly" ? [...weekdays].sort((a, b) => a - b) : [],
      interval_days: frequency === "interval" ? intervalDays : null,
      enabled,
    };
    try {
      if (task) {
        await api.updateSchedule(task.id, input);
      } else {
        await api.createSchedule(input);
      }
      haptic("medium");
      onSaved();
      onClose();
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.isForbidden
          ? "Not allowed."
          : "Failed to save.",
      );
    }
  }

  const headerTitle = title.trim() || (task ? "Edit reminder" : "New reminder");

  if (!mounted) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label={task ? "Edit reminder" : "New reminder"}
    >
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div className="animate-fade-in relative flex max-h-[92vh] w-full max-w-md flex-col overflow-hidden rounded-t-card-lg border border-border bg-surface shadow-pop sm:rounded-card-lg">
        {/* Header: back, title + step counter, close */}
        <div className="flex items-center gap-2 px-5 pt-5">
          {visibleIndex > 0 ? (
            <button
              type="button"
              onClick={goBack}
              aria-label="Back"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted transition active:bg-surface-2"
            >
              <ChevronLeft className="h-5 w-5" aria-hidden />
            </button>
          ) : (
            <span className="h-9 w-9 shrink-0" aria-hidden />
          )}
          <div className="min-w-0 flex-1 text-center">
            <p className="truncate text-sm font-bold text-text">{headerTitle}</p>
            <p className="text-xs text-muted">
              Step {visibleIndex + 1} of {visibleTotal}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-muted transition active:bg-surface-2"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>

        {/* Progress bar */}
        <div className="flex gap-1.5 px-5 pt-4">
          {Array.from({ length: visibleTotal }, (_, i) => (
            <span
              key={i}
              className={`h-1.5 flex-1 rounded-full transition ${
                i <= visibleIndex ? "bg-primary" : "bg-surface-2"
              }`}
            />
          ))}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-5">
          {step === 1 && (
            <div className="space-y-4">
              <Field label="Title">
                <Input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="Workout check-in"
                  aria-label="Title"
                />
              </Field>
              <Field label="Prompt">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  rows={4}
                  placeholder="Ask me how my workout went and check my progress"
                  aria-label="Prompt"
                  className={textareaClass}
                />
              </Field>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-5">
              <div className="grid grid-cols-2 gap-3">
                {FREQ_CARDS.map((card) => {
                  const active = frequency === card.value;
                  const Icon = card.icon;
                  return (
                    <button
                      key={card.value}
                      type="button"
                      aria-pressed={active}
                      onClick={() => {
                        hapticSelection();
                        setFrequency(card.value);
                      }}
                      className={`flex flex-col items-start gap-2 rounded-2xl border p-4 text-left transition active:scale-[0.98] ${
                        active
                          ? "border-primary bg-primary/10 shadow-soft"
                          : "border-border bg-surface-2/50"
                      }`}
                    >
                      <span
                        className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                          active ? "bg-primary text-primary-fg" : "bg-surface-3 text-muted"
                        }`}
                      >
                        <Icon className="h-4 w-4" aria-hidden />
                      </span>
                      <span
                        className={`text-sm font-semibold ${active ? "text-primary" : "text-text"}`}
                      >
                        {card.title}
                      </span>
                      <span className="text-xs text-muted">{card.hint}</span>
                    </button>
                  );
                })}
              </div>

              {/* Weekly → weekday chips */}
              {frequency === "weekly" && (
                <div>
                  <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted">
                    Days
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {WEEKDAY_LABELS.map((label, day) => {
                      const active = weekdays.includes(day);
                      return (
                        <button
                          key={day}
                          type="button"
                          aria-pressed={active}
                          onClick={() => toggleWeekday(day)}
                          className={`rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                            active
                              ? "bg-primary text-primary-fg shadow-soft"
                              : "border border-border bg-surface-2/60 text-muted active:bg-surface-2"
                          }`}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Interval → number stepper */}
              {frequency === "interval" && (
                <div>
                  <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted">
                    Interval
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-muted">every</span>
                    <Stepper
                      value={intervalDays}
                      min={1}
                      max={30}
                      onChange={setIntervalDays}
                      label="Interval days"
                    />
                    <span className="text-sm text-muted">days</span>
                  </div>
                </div>
              )}

              {/* Times-per-day selector (hidden for as_needed) */}
              {!isAsNeeded && (
                <Field label="Times per day">
                  <SegmentedControl
                    options={COUNT_OPTIONS}
                    value={String(times.length)}
                    onChange={(v) => setCount(parseInt(v, 10))}
                  />
                </Field>
              )}
            </div>
          )}

          {step === 3 && !isAsNeeded && (
            <div className="space-y-3">
              {times.map((t, i) => {
                const tod = timeOfDay(t);
                const Icon = TIME_OF_DAY_ICON[tod.key];
                return (
                  <div
                    key={i}
                    className="flex items-center gap-3 rounded-2xl border border-border bg-surface-2/50 p-3"
                  >
                    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" aria-hidden />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-text">{tod.label}</p>
                      <p className="text-xs text-muted">
                        Reminder {i + 1} of {times.length}
                      </p>
                    </div>
                    <TimeChipPicker value={t} onChange={(v) => setTimeAt(i, v)} />
                  </div>
                );
              })}
            </div>
          )}

          {step === 4 && (
            <div className="space-y-4">
              <div className="rounded-2xl border border-border bg-surface-2/50 p-4">
                <p className="text-base font-bold text-text">
                  {title.trim() || "Untitled"}
                </p>
                <p className="mt-0.5 text-sm text-muted">{reviewFrequencyLabel}</p>
                {!isAsNeeded && times.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {times.map((t, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-primary/12 px-2.5 py-1 text-xs font-semibold text-primary"
                      >
                        {timeChip(t)}
                      </span>
                    ))}
                  </div>
                )}
                {prompt.trim() && (
                  <p className="mt-3 border-t border-border pt-3 text-xs leading-relaxed text-muted [overflow-wrap:anywhere]">
                    {prompt.trim()}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text">Enabled</p>
                  <p className="text-xs text-muted">
                    Turn off to pause without deleting.
                  </p>
                </div>
                <Toggle checked={enabled} onChange={setEnabled} label="Enabled" />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-border px-5 py-4">
          {message && (
            <div className="mb-3 flex justify-end">
              <SaveMessage status={status} message={message} />
            </div>
          )}
          {step === 4 ? (
            <Button
              onClick={save}
              disabled={status === "saving" || !step1Valid}
              icon={Save}
              full
            >
              {status === "saving" ? "Saving…" : "Save"}
            </Button>
          ) : (
            <Button
              onClick={goNext}
              disabled={(step === 1 && !step1Valid) || (step === 2 && !step2Valid)}
              full
            >
              Continue
            </Button>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}

// ---------------------------------------------------------------------------
// Small number stepper
// ---------------------------------------------------------------------------

function Stepper({
  value,
  min,
  max,
  onChange,
  label,
}: {
  value: number;
  min: number;
  max: number;
  onChange: (n: number) => void;
  label: string;
}) {
  function bump(delta: number) {
    const next = Math.min(max, Math.max(min, value + delta));
    if (next !== value) {
      haptic("light");
      onChange(next);
    }
  }
  return (
    <div
      className="inline-flex items-center gap-3 rounded-full border border-border bg-surface px-2 py-1"
      role="group"
      aria-label={label}
    >
      <button
        type="button"
        onClick={() => bump(-1)}
        disabled={value <= min}
        aria-label="Decrease"
        className="flex h-8 w-8 items-center justify-center rounded-full text-text transition active:bg-surface-2 disabled:opacity-40"
      >
        −
      </button>
      <span className="min-w-[1.5rem] text-center text-sm font-bold text-text tabular-nums">
        {value}
      </span>
      <button
        type="button"
        onClick={() => bump(1)}
        disabled={value >= max}
        aria-label="Increase"
        className="flex h-8 w-8 items-center justify-center rounded-full text-text transition active:bg-surface-2 disabled:opacity-40"
      >
        +
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tappable time chip → expands an hour/minute picker (two Selects)
// ---------------------------------------------------------------------------

function TimeChipPicker({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const { hour, minute } = useMemo(() => splitTime(value), [value]);

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => {
          hapticSelection();
          setOpen(true);
        }}
        className="shrink-0 rounded-full bg-primary/12 px-3.5 py-2 text-sm font-bold text-primary transition active:scale-[0.97]"
      >
        {timeChip(value)}
      </button>
    );
  }

  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <Select
        options={HOUR_OPTIONS}
        value={hour}
        onChange={(h) => onChange(`${h}:${minute}`)}
        className="w-[4.5rem]"
      />
      <span className="text-sm font-semibold text-muted" aria-hidden>
        :
      </span>
      <Select
        options={MINUTE_OPTIONS}
        value={minute}
        onChange={(m) => onChange(`${hour}:${m}`)}
        className="w-[4.5rem]"
      />
      <button
        type="button"
        onClick={() => {
          hapticSelection();
          setOpen(false);
        }}
        aria-label="Done"
        className="flex h-9 w-9 items-center justify-center rounded-full text-primary transition active:bg-surface-2"
      >
        <X className="h-4 w-4" aria-hidden />
      </button>
    </div>
  );
}
