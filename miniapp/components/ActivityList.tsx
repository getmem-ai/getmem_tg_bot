import { Bot, MessageSquare, User as UserIcon } from "lucide-react";
import type { ActivityItem } from "@/lib/types";
import { relativeTime, truncate } from "@/lib/format";
import { Card } from "./Card";
import { EmptyState } from "./ui";

interface ActivityListProps {
  items: ActivityItem[];
}

function RoleAvatar({ role }: { role: ActivityItem["role"] }) {
  const isAssistant = role === "assistant";
  const Icon = isAssistant ? Bot : UserIcon;
  return (
    <span
      className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
        isAssistant
          ? "bg-tg-button/12 text-tg-button"
          : "bg-tg-hint/12 text-tg-hint"
      }`}
    >
      <Icon className="h-4 w-4" aria-hidden />
    </span>
  );
}

export function ActivityList({ items }: ActivityListProps) {
  if (items.length === 0) {
    return (
      <Card>
        <EmptyState
          icon={MessageSquare}
          title="No activity yet"
          hint="Your recent messages with the bot will show up here."
        />
      </Card>
    );
  }

  return (
    <Card>
      <ul className="-mx-1 divide-y divide-black/[0.05] dark:divide-white/[0.06]">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-3 px-1 py-3">
            <RoleAvatar role={item.role} />
            <div className="min-w-0 flex-1">
              <p className="break-words text-sm leading-snug text-tg-text">
                {truncate(item.content, 160)}
              </p>
              <p className="mt-1 flex items-center gap-1.5 text-xs text-tg-hint">
                <span>{relativeTime(item.created_at)}</span>
                {item.model && (
                  <>
                    <span aria-hidden>·</span>
                    <span className="truncate">{item.model}</span>
                  </>
                )}
              </p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
