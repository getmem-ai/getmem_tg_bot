"use client";

import { useMemo, useState } from "react";
import {
  AlarmClock,
  CalendarOff,
  Pencil,
  Plus,
  Save,
  Trash2,
  X,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type {
  ScheduleInput,
  ScheduleRunsResponse,
  ScheduledTask,
  SchedulesResponse,
} from "@/lib/types";
import { haptic } from "@/lib/telegram";
import { truncate } from "@/lib/format";
import { PageHeader, Card, SectionTitle } from "./Card";
import { CardSkeleton } from "./Skeleton";
import { ErrorState } from "./ErrorState";
import {
  Button,
  EmptyState,
  Field,
  Input,
  SaveMessage,
  SegmentedControl,
  Toggle,
  type SaveStatus,
} from "./ui";

const MAX_TIMES = 6;

// Weekday labels — index 0 = Monday … 6 = Sunday (matches the contract).
const WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

type Frequency = "daily" | "weekly";

const FREQUENCIES: { value: Frequency; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
];

const textareaClass =
  "w-full resize-y rounded-2xl border border-border bg-surface-2/60 p-3 text-sm text-text outline-none transition placeholder:text-muted focus:border-primary focus:bg-surface focus:shadow-ring";

/** Formats an ISO timestamp into the user's timezone, e.g. "Jun 14, 08:00". */
function formatInTz(iso: string | null, tz: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  try {
    return d.toLocaleString(undefined, {
      timeZone: tz,
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    // Invalid tz — fall back to local time.
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}

/** Human summary of a task's schedule, e.g. "Daily · 08:00, 20:00". */
function scheduleSummary(task: ScheduledTask): string {
  const times = task.times.length ? task.times.join(", ") : "—";
  if (task.frequency === "weekly") {
    const days = [...task.weekdays]
      .sort((a, b) => a - b)
      .map((d) => WEEKDAY_LABELS[d])
      .filter(Boolean);
    const dayPart = days.length ? days.join(", ") : "No days";
    return `${dayPart} · ${times}`;
  }
  return `Daily · ${times}`;
}

interface FormState {
  editingId: number | null;
  title: string;
  prompt: string;
  frequency: Frequency;
  times: string[];
  weekdays: number[];
  enabled: boolean;
}

const EMPTY_FORM: FormState = {
  editingId: null,
  title: "",
  prompt: "",
  frequency: "daily",
  times: ["08:00"],
  weekdays: [],
  enabled: true,
};

export function SchedulesTab() {
  const { data, error, loading, reload } = useApi<SchedulesResponse>(() =>
    api.getSchedules(),
  );

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Schedules"
        subtitle="Reminders the bot runs for you"
        icon={AlarmClock}
      />
      {loading ? (
        <CardSkeleton lines={4} />
      ) : error ? (
        <ErrorState error={error} onRetry={reload} />
      ) : data ? (
        data.enabled ? (
          <SchedulesView data={data} onChanged={reload} />
        ) : (
          <Card>
            <EmptyState
              icon={CalendarOff}
              title="Scheduling is turned off by the operator."
              hint="Recurring reminders aren't available right now."
            />
          </Card>
        )
      ) : null}
    </div>
  );
}

function SchedulesView({
  data,
  onChanged,
}: {
  data: SchedulesResponse;
  onChanged: () => void;
}) {
  const tz = data.timezone || "UTC";
  const [tasks, setTasks] = useState<ScheduledTask[]>(data.tasks);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  const runs = useApi<ScheduleRunsResponse>(() => api.getScheduleRuns());

  // Sort upcoming: enabled tasks with a next run first (soonest), then disabled
  // / null-next tasks last.
  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) => {
      const aKey = a.enabled && a.next_run_at ? a.next_run_at : null;
      const bKey = b.enabled && b.next_run_at ? b.next_run_at : null;
      if (aKey && bKey) return aKey < bKey ? -1 : aKey > bKey ? 1 : 0;
      if (aKey) return -1;
      if (bKey) return 1;
      return 0;
    });
  }, [tasks]);

  function setField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function resetForm() {
    setForm(EMPTY_FORM);
  }

  function addTime() {
    setForm((f) =>
      f.times.length >= MAX_TIMES ? f : { ...f, times: [...f.times, "09:00"] },
    );
  }

  function removeTime(index: number) {
    setForm((f) =>
      f.times.length <= 1
        ? f
        : { ...f, times: f.times.filter((_, i) => i !== index) },
    );
  }

  function setTime(index: number, value: string) {
    setForm((f) => ({
      ...f,
      times: f.times.map((t, i) => (i === index ? value : t)),
    }));
  }

  function toggleWeekday(day: number) {
    setForm((f) => ({
      ...f,
      weekdays: f.weekdays.includes(day)
        ? f.weekdays.filter((d) => d !== day)
        : [...f.weekdays, day],
    }));
  }

  function loadIntoForm(task: ScheduledTask) {
    haptic("light");
    setStatus("idle");
    setMessage("");
    setForm({
      editingId: task.id,
      title: task.title,
      prompt: task.prompt,
      frequency: task.frequency === "weekly" ? "weekly" : "daily",
      times: task.times.length ? [...task.times] : ["08:00"],
      weekdays: [...task.weekdays],
      enabled: task.enabled,
    });
  }

  function validate(): string | null {
    if (!form.title.trim()) return "Give it a title.";
    if (!form.prompt.trim()) return "Add what the bot should ask or do.";
    if (form.times.length < 1) return "Add at least one time.";
    if (form.frequency === "weekly" && form.weekdays.length < 1)
      return "Pick at least one weekday.";
    return null;
  }

  async function save() {
    const err = validate();
    if (err) {
      setStatus("error");
      setMessage(err);
      return;
    }
    setStatus("saving");
    setMessage("");
    const input: ScheduleInput = {
      title: form.title.trim(),
      prompt: form.prompt.trim(),
      frequency: form.frequency,
      times: form.times,
      weekdays: form.frequency === "weekly" ? [...form.weekdays].sort((a, b) => a - b) : [],
      enabled: form.enabled,
    };
    try {
      if (form.editingId != null) {
        const updated = await api.updateSchedule(form.editingId, input);
        setTasks((prev) =>
          prev.map((t) => (t.id === updated.id ? updated : t)),
        );
      } else {
        const created = await api.createSchedule(input);
        setTasks((prev) => [created, ...prev]);
      }
      haptic("medium");
      resetForm();
      setStatus("saved");
      setMessage("Saved");
      window.setTimeout(() => setStatus("idle"), 2000);
      onChanged();
    } catch (e: unknown) {
      setStatus("error");
      setMessage(
        e instanceof ApiError && e.isForbidden ? "Not allowed." : "Failed to save.",
      );
    }
  }

  async function toggleEnabled(task: ScheduledTask, enabled: boolean) {
    // Optimistic flip; revert on failure.
    setTasks((prev) =>
      prev.map((t) => (t.id === task.id ? { ...t, enabled } : t)),
    );
    try {
      const updated = await api.updateSchedule(task.id, {
        title: task.title,
        prompt: task.prompt,
        frequency: task.frequency,
        times: task.times,
        weekdays: task.weekdays,
        enabled,
      });
      setTasks((prev) =>
        prev.map((t) => (t.id === updated.id ? updated : t)),
      );
    } catch {
      setTasks((prev) =>
        prev.map((t) =>
          t.id === task.id ? { ...t, enabled: task.enabled } : t,
        ),
      );
    }
  }

  async function remove(task: ScheduledTask) {
    if (!window.confirm(`Delete "${task.title}"?`)) return;
    haptic("medium");
    try {
      await api.deleteSchedule(task.id);
      setTasks((prev) => prev.filter((t) => t.id !== task.id));
      if (form.editingId === task.id) resetForm();
    } catch {
      // Non-fatal — leave the row in place.
    }
  }

  const saving = status === "saving";

  return (
    <div className="flex flex-col gap-4">
      {/* Create / edit form */}
      <Card>
        <SectionTitle icon={form.editingId != null ? Pencil : Plus}>
          {form.editingId != null ? "Edit reminder" : "New reminder"}
        </SectionTitle>
        <div className="space-y-4">
          <Field label="Title">
            <Input
              value={form.title}
              onChange={(e) => setField("title", e.target.value)}
              placeholder="Workout check-in"
              aria-label="Title"
            />
          </Field>

          <Field label="Prompt">
            <textarea
              value={form.prompt}
              onChange={(e) => setField("prompt", e.target.value)}
              rows={3}
              placeholder="Ask me how my workout went and check my progress"
              aria-label="Prompt"
              className={textareaClass}
            />
          </Field>

          <Field label="Frequency">
            <SegmentedControl
              options={FREQUENCIES}
              value={form.frequency}
              onChange={(v) => setField("frequency", v)}
            />
          </Field>

          {/* Times editor */}
          <div>
            <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted">
              Times
            </span>
            <div className="space-y-2">
              {form.times.map((t, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="time"
                    value={t}
                    onChange={(e) => setTime(i, e.target.value)}
                    aria-label={`Time ${i + 1}`}
                    className="flex-1 rounded-2xl border border-border bg-surface-2/60 px-3.5 py-2.5 text-sm text-text outline-none transition focus:border-primary focus:bg-surface focus:shadow-ring"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      haptic("light");
                      removeTime(i);
                    }}
                    disabled={form.times.length <= 1}
                    aria-label="Remove time"
                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-border text-muted transition active:bg-surface-2 disabled:opacity-40"
                  >
                    <X className="h-4 w-4" aria-hidden />
                  </button>
                </div>
              ))}
            </div>
            {form.times.length < MAX_TIMES && (
              <Button
                variant="secondary"
                size="sm"
                icon={Plus}
                onClick={addTime}
                className="mt-2"
              >
                Add time
              </Button>
            )}
          </div>

          {/* Weekdays — only for weekly */}
          {form.frequency === "weekly" && (
            <div>
              <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted">
                Days
              </span>
              <div className="flex flex-wrap gap-1.5">
                {WEEKDAY_LABELS.map((label, day) => {
                  const active = form.weekdays.includes(day);
                  return (
                    <button
                      key={day}
                      type="button"
                      aria-pressed={active}
                      onClick={() => {
                        haptic("light");
                        toggleWeekday(day);
                      }}
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

          <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-text">Enabled</p>
              <p className="text-xs text-muted">
                Turn off to pause without deleting.
              </p>
            </div>
            <Toggle
              checked={form.enabled}
              onChange={(v) => setField("enabled", v)}
              label="Enabled"
            />
          </div>
        </div>

        <div className="mt-4 flex items-center justify-between gap-3">
          <SaveMessage status={status} message={message} />
          <div className="flex items-center gap-2">
            {form.editingId != null && (
              <Button variant="secondary" size="sm" onClick={resetForm}>
                Cancel
              </Button>
            )}
            <Button onClick={save} disabled={saving} icon={Save} size="sm">
              {saving ? "Saving…" : form.editingId != null ? "Update" : "Create"}
            </Button>
          </div>
        </div>
      </Card>

      {/* Upcoming */}
      <Card>
        <SectionTitle icon={AlarmClock}>Upcoming</SectionTitle>
        <p className="mb-3 text-xs text-muted">
          Times are in your timezone ({tz}). Change it in your profile.
        </p>
        {sortedTasks.length === 0 ? (
          <EmptyState
            icon={AlarmClock}
            title="No reminders yet"
            hint="Create one above and the bot will message you on schedule."
          />
        ) : (
          <ul className="space-y-2">
            {sortedTasks.map((task) => (
              <li
                key={task.id}
                className="flex items-start gap-3 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3"
              >
                <div className="min-w-0 flex-1">
                  <p
                    className={`truncate text-sm font-medium ${task.enabled ? "text-text" : "text-muted"}`}
                  >
                    {task.title}
                  </p>
                  <p className="truncate text-xs text-muted">
                    {scheduleSummary(task)}
                  </p>
                  {task.enabled && task.next_run_at && (
                    <p className="mt-0.5 truncate text-xs text-muted">
                      Next: {formatInTz(task.next_run_at, tz)}
                    </p>
                  )}
                </div>
                <div className="flex shrink-0 flex-col items-end gap-2">
                  <Toggle
                    checked={task.enabled}
                    onChange={(v) => toggleEnabled(task, v)}
                    label={`Toggle ${task.title}`}
                  />
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => loadIntoForm(task)}
                      aria-label={`Edit ${task.title}`}
                      className="flex h-8 w-8 items-center justify-center rounded-xl text-muted transition active:bg-surface-2"
                    >
                      <Pencil className="h-4 w-4" aria-hidden />
                    </button>
                    <button
                      type="button"
                      onClick={() => remove(task)}
                      aria-label={`Delete ${task.title}`}
                      className="flex h-8 w-8 items-center justify-center rounded-xl text-danger transition active:bg-danger/10"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Card>

      {/* Recent runs */}
      <Card>
        <SectionTitle icon={AlarmClock}>Recent runs</SectionTitle>
        {runs.loading ? (
          <CardSkeleton lines={3} />
        ) : runs.error ? (
          <ErrorState error={runs.error} onRetry={runs.reload} />
        ) : runs.data && runs.data.runs.length > 0 ? (
          <ul className="space-y-2">
            {runs.data.runs.map((run) => {
              const ok = run.status === "sent";
              return (
                <li
                  key={run.id}
                  className="flex items-start gap-3 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3"
                >
                  <span
                    aria-hidden
                    className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${ok ? "bg-success" : "bg-danger"}`}
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs text-muted">
                      {formatInTz(run.fired_at, tz)}
                    </p>
                    {run.preview && (
                      <p className="mt-0.5 text-sm text-text [overflow-wrap:anywhere]">
                        {truncate(run.preview, 120)}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        ) : (
          <EmptyState
            icon={AlarmClock}
            title="No runs yet"
            hint="Once a reminder fires, it'll show up here."
          />
        )}
      </Card>
    </div>
  );
}
