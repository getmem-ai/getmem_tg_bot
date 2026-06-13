"use client";

import { api, type ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { AdminStatsResponse, RecentUser } from "@/lib/types";
import { formatDate, formatNumber } from "@/lib/format";
import { Card, SectionTitle } from "./Card";
import { CardSkeleton } from "./Skeleton";
import { ErrorState } from "./ErrorState";
import { PromptEditor } from "./PromptEditor";

interface StatProps {
  label: string;
  value: number;
  icon: string;
}

function Stat({ label, value, icon }: StatProps) {
  return (
    <div className="rounded-xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-bg/40 p-3">
      <div className="text-lg" aria-hidden>
        {icon}
      </div>
      <div className="mt-1 text-xl font-bold leading-none">
        {formatNumber(value)}
      </div>
      <div className="mt-1 text-[11px] text-tg-hint">{label}</div>
    </div>
  );
}

function RecentUserRow({ user }: { user: RecentUser }) {
  const isPremium = user.tier === "premium";
  return (
    <li className="flex items-center justify-between gap-3 py-2">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium text-tg-text">
          {user.first_name}
          {isPremium && <span className="ml-1" aria-hidden>⭐</span>}
        </p>
        {user.username && (
          <p className="truncate text-xs text-tg-hint">@{user.username}</p>
        )}
      </div>
      <span className="shrink-0 text-xs text-tg-hint">
        {formatDate(user.created_at)}
      </span>
    </li>
  );
}

/** Admin-only global stats. Fetches /admin/stats lazily (only when rendered). */
export function AdminPanel() {
  const { data, error, loading, reload } = useApi<AdminStatsResponse>(
    () => api.adminStats(),
    true,
  );

  return (
    <div className="space-y-3">
      <SectionTitle>Admin · global stats</SectionTitle>

      {loading && <CardSkeleton lines={4} />}

      {error && <AdminError error={error} onRetry={reload} />}

      {data && (
        <>
          <div className="grid grid-cols-2 gap-3">
            <Stat label="Users" value={data.users} icon="👥" />
            <Stat label="Premium" value={data.premium} icon="⭐" />
            <Stat label="Messages today" value={data.messages_today} icon="💬" />
            <Stat label="Payments" value={data.payments} icon="💳" />
          </div>

          <Card>
            <SectionTitle>Recent users</SectionTitle>
            {data.recent_users.length === 0 ? (
              <p className="py-4 text-center text-sm text-tg-hint">No users yet</p>
            ) : (
              <ul className="divide-y divide-black/[0.05] dark:divide-white/[0.06]">
                {data.recent_users.map((u) => (
                  <RecentUserRow key={u.id} user={u} />
                ))}
              </ul>
            )}
          </Card>

          <PromptEditor />
        </>
      )}
    </div>
  );
}

function AdminError({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  if (error.isForbidden) {
    return (
      <Card>
        <p className="text-sm text-tg-hint">
          Admin stats are not available for this account.
        </p>
      </Card>
    );
  }
  return <ErrorState error={error} onRetry={onRetry} />;
}
