"use client";

import { useMemo, useState } from "react";
import {
  AlarmClock,
  Bot,
  CalendarOff,
  Clock,
  Plus,
  Trash2,
} from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type {
  ScheduleInput,
  ScheduleRunsResponse,
  ScheduledTask,
  SchedulesResponse,
} from "@/lib/types";
import { haptic } from "@/lib/telegram";
import { formatDate, truncate } from "@/lib/format";
import {
  dayLabel,
  frequencyLabel,
  occursOnDay,
  timeChip,
  timeChips,
} from "@/lib/schedule";
import { PageHeader, Card, SectionTitle } from "./Card";
import { CardSkeleton } from "./Skeleton";
import { ErrorState } from "./ErrorState";
import { ScheduleCalendar } from "./ScheduleCalendar";
import { ScheduleWizard } from "./ScheduleWizard";
import { Button, EmptyState, Toggle } from "./ui";

/** Builds the full ScheduleInput payload from an existing task (for toggles). */
function inputFromTask(task: ScheduledTask, enabled: boolean): ScheduleInput {
  return {
    title: task.title,
    prompt: task.prompt,
    frequency: task.frequency,
    times: task.times,
    weekdays: task.weekdays,
    interval_days: task.interval_days,
    enabled,
  };
}

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
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
}

export function SchedulesTab() {
  const { data, error, loading, reload } = useApi<SchedulesResponse>(() =>
    api.getSchedules(),
  );

  const count = data?.tasks.length ?? 0;

  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Schedules"
        subtitle={count > 0 ? `${count} reminder${count > 1 ? "s" : ""}` : "Reminders the bot runs for you"}
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
  const [editing, setEditing] = useState<ScheduledTask | null>(null);
  const [wizardOpen, setWizardOpen] = useState(false);
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);

  const runs = useApi<ScheduleRunsResponse>(() => api.getScheduleRuns());

  // Reminders that fall on the tapped calendar day (across active tasks).
  const dayReminders = useMemo(() => {
    if (!selectedDay) return [];
    const out: { task: ScheduledTask; time: string }[] = [];
    for (const task of tasks) {
      if (!task.enabled || task.frequency === "as_needed") continue;
      if (occursOnDay(task, selectedDay) === 0) continue;
      for (const t of task.times) out.push({ task, time: t });
    }
    out.sort((a, b) => a.time.localeCompare(b.time));
    return out;
  }, [selectedDay, tasks]);

  function openNew() {
    haptic("medium");
    setEditing(null);
    setWizardOpen(true);
  }

  function openEdit(task: ScheduledTask) {
    haptic("light");
    setEditing(task);
    setWizardOpen(true);
  }

  function closeWizard() {
    setWizardOpen(false);
    setEditing(null);
  }

  // Re-fetch after a wizard save so optimistic local state stays consistent.
  function afterSaved() {
    onChanged();
    api
      .getSchedules()
      .then((fresh) => setTasks(fresh.tasks))
      .catch(() => {});
    runs.reload();
  }

  async function toggleEnabled(task: ScheduledTask, enabled: boolean) {
    setTasks((prev) => prev.map((t) => (t.id === task.id ? { ...t, enabled } : t)));
    try {
      const updated = await api.updateSchedule(task.id, inputFromTask(task, enabled));
      setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
    } catch {
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, enabled: task.enabled } : t)),
      );
    }
  }

  async function remove(task: ScheduledTask) {
    if (!window.confirm(`Delete "${task.title}"?`)) return;
    haptic("medium");
    try {
      await api.deleteSchedule(task.id);
      setTasks((prev) => prev.filter((t) => t.id !== task.id));
      onChanged();
    } catch {
      // Non-fatal — leave the row in place.
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {/* Top action — create a new reminder (opens the wizard). */}
      <div className="flex justify-end">
        <Button onClick={openNew} icon={Plus} size="sm">
          New reminder
        </Button>
      </div>

      {/* Nudge: timezone still on UTC → reminders won't fire in local time */}
      {tz === "UTC" && (
        <div className="flex items-start gap-3 rounded-2xl border border-border bg-surface-2/60 p-4">
          <span
            aria-hidden
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary"
          >
            <Clock className="h-4 w-4" />
          </span>
          <p className="text-sm leading-relaxed text-text">
            Your timezone is set to UTC —{" "}
            <span className="font-semibold text-primary">
              set your real timezone in your profile
            </span>{" "}
            (Home → edit profile) so reminders fire in your local time.
          </p>
        </div>
      )}

      {/* Calendar */}
      <Card>
        <ScheduleCalendar
          tasks={tasks}
          selected={selectedDay}
          onSelect={setSelectedDay}
        />
        {selectedDay && (
          <div className="mt-4 border-t border-border pt-4">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">
              {dayLabel(selectedDay)}
            </p>
            {dayReminders.length === 0 ? (
              <p className="text-sm text-muted">No reminders this day.</p>
            ) : (
              <ul className="space-y-1.5">
                {dayReminders.map((r, i) => (
                  <li
                    key={`${r.task.id}-${i}`}
                    className="flex items-center justify-between gap-3 rounded-xl bg-surface-2/50 px-3 py-2"
                  >
                    <span className="min-w-0 truncate text-sm text-text">
                      {r.task.title}
                    </span>
                    <span className="shrink-0 text-xs font-semibold text-primary">
                      {timeChip(r.time)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </Card>

      {/* Active reminders */}
      <Card>
        <SectionTitle icon={AlarmClock}>Active</SectionTitle>
        {tasks.length === 0 ? (
          <EmptyState
            icon={AlarmClock}
            title="No reminders yet"
            hint="Tap “New reminder” above and the bot will message you on schedule."
          />
        ) : (
          <ul className="space-y-2.5">
            {tasks.map((task) => {
              const chips = timeChips(task.times);
              return (
                <li
                  key={task.id}
                  className="rounded-2xl border border-border bg-surface-2/40 p-3.5"
                >
                  <div className="flex items-start gap-3">
                    <button
                      type="button"
                      onClick={() => openEdit(task)}
                      aria-label={`Edit ${task.title}`}
                      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-grad-primary text-primary-fg shadow-soft"
                    >
                      <Bot className="h-5 w-5" aria-hidden />
                    </button>
                    <button
                      type="button"
                      onClick={() => openEdit(task)}
                      className="min-w-0 flex-1 text-left"
                    >
                      <p
                        className={`truncate text-sm font-semibold ${task.enabled ? "text-text" : "text-muted"}`}
                      >
                        {task.title}
                      </p>
                      <p className="truncate text-xs text-muted">
                        {frequencyLabel(task)}
                      </p>
                      {chips.length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {chips.map((c, i) => (
                            <span
                              key={i}
                              className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary"
                            >
                              {c}
                            </span>
                          ))}
                        </div>
                      )}
                    </button>
                    <Toggle
                      checked={task.enabled}
                      onChange={(v) => toggleEnabled(task, v)}
                      label={`Toggle ${task.title}`}
                    />
                  </div>
                  <div className="mt-2.5 flex items-center justify-between gap-3 border-t border-border pt-2.5">
                    <span className="truncate text-[11px] text-muted">
                      {formatDate(task.created_at)} · ongoing
                    </span>
                    <button
                      type="button"
                      onClick={() => remove(task)}
                      aria-label={`Delete ${task.title}`}
                      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-danger transition active:bg-danger/10"
                    >
                      <Trash2 className="h-4 w-4" aria-hidden />
                    </button>
                  </div>
                </li>
              );
            })}
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
                    <p className="text-xs text-muted">{formatInTz(run.fired_at, tz)}</p>
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

      {wizardOpen && (
        <ScheduleWizard
          task={editing}
          onClose={closeWizard}
          onSaved={afterSaved}
        />
      )}
    </div>
  );
}
