import { Fragment } from "react";
import { Bot, MessageSquare, User as UserIcon } from "lucide-react";
import type { ActivityItem } from "@/lib/types";
import { dayLabel, relativeTime, shortModel } from "@/lib/format";
import { EmptyState } from "./ui";

interface ActivityListProps {
  items: ActivityItem[];
}

interface DayGroup {
  label: string;
  items: ActivityItem[];
}

/** Buckets items into contiguous day groups, preserving incoming order. */
function groupByDay(items: ActivityItem[]): DayGroup[] {
  const groups: DayGroup[] = [];
  for (const item of items) {
    const label = dayLabel(item.created_at);
    const last = groups[groups.length - 1];
    if (last && last.label === label) {
      last.items.push(item);
    } else {
      groups.push({ label, items: [item] });
    }
  }
  return groups;
}

function DayHeader({ label }: { label: string }) {
  return (
    <div className="sticky top-2 z-10 -mx-1 mb-2 flex justify-center">
      <span className="rounded-full border border-black/[0.06] bg-tg-bg/80 px-3 py-1 text-[11px] font-semibold uppercase tracking-wide text-tg-hint shadow-sm backdrop-blur dark:border-white/[0.08]">
        {label}
      </span>
    </div>
  );
}

function MessageBubble({ item }: { item: ActivityItem }) {
  const isAssistant = item.role === "assistant";
  const Icon = isAssistant ? Bot : UserIcon;

  return (
    <div className={`flex flex-col ${isAssistant ? "items-start" : "items-end"}`}>
      {/* Author row */}
      <div
        className={`mb-1 flex items-center gap-1.5 px-1 text-[11px] font-medium text-tg-hint ${
          isAssistant ? "" : "flex-row-reverse"
        }`}
      >
        <span
          className={`flex h-5 w-5 items-center justify-center rounded-md ${
            isAssistant
              ? "bg-tg-button/12 text-tg-button"
              : "bg-tg-hint/15 text-tg-hint"
          }`}
        >
          <Icon className="h-3 w-3" aria-hidden />
        </span>
        <span>{isAssistant ? "Assistant" : "You"}</span>
        <span aria-hidden>·</span>
        <span>{relativeTime(item.created_at)}</span>
      </div>

      {/* Bubble */}
      <div
        className={`max-w-[88%] rounded-2xl border px-3.5 py-2.5 shadow-sm shadow-black/[0.02] ${
          isAssistant
            ? "rounded-tl-md border-black/[0.06] bg-tg-secondary/70 dark:border-white/[0.08]"
            : "rounded-tr-md border-tg-button/20 bg-tg-button/10"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-tg-text [overflow-wrap:anywhere]">
          {item.content}
        </p>
        {isAssistant && item.model && (
          <span className="mt-1.5 inline-flex max-w-full items-center rounded-md bg-tg-hint/10 px-1.5 py-0.5 text-[10px] font-medium text-tg-hint">
            <span className="truncate">{shortModel(item.model)}</span>
          </span>
        )}
      </div>
    </div>
  );
}

export function ActivityList({ items }: ActivityListProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={MessageSquare}
        title="No messages yet"
        hint="Say hi to the bot and your conversation will show up here."
      />
    );
  }

  const groups = groupByDay(items);

  return (
    <div className="flex flex-col gap-2">
      {groups.map((group, gi) => (
        <Fragment key={`${group.label}-${gi}`}>
          <DayHeader label={group.label} />
          <div className="flex flex-col gap-3">
            {group.items.map((item, i) => (
              <MessageBubble key={`${gi}-${i}`} item={item} />
            ))}
          </div>
        </Fragment>
      ))}
    </div>
  );
}
