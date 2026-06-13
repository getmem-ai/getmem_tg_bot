import type { ActivityItem } from "@/lib/types";
import { relativeTime, truncate } from "@/lib/format";
import { Card, SectionTitle } from "./Card";

interface ActivityListProps {
  items: ActivityItem[];
}

function roleIcon(role: ActivityItem["role"]): string {
  return role === "assistant" ? "🤖" : "🧑";
}

export function ActivityList({ items }: ActivityListProps) {
  return (
    <Card>
      <SectionTitle>Recent activity</SectionTitle>

      {items.length === 0 ? (
        <p className="py-6 text-center text-sm text-tg-hint">No activity yet</p>
      ) : (
        <ul className="-mx-1 divide-y divide-black/[0.05] dark:divide-white/[0.06]">
          {items.map((item, i) => (
            <li key={i} className="flex items-start gap-3 px-1 py-2.5">
              <span className="mt-0.5 text-base leading-none" aria-hidden>
                {roleIcon(item.role)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="break-words text-sm text-tg-text">
                  {truncate(item.content, 120)}
                </p>
                <p className="mt-0.5 text-xs text-tg-hint">
                  {relativeTime(item.created_at)}
                  {item.model ? ` · ${item.model}` : ""}
                </p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}
