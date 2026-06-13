"use client";

import type { ComponentType } from "react";
import { Crown, CreditCard, MessageSquare, Users } from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { AdminStatsResponse, RecentUser } from "@/lib/types";
import { formatDate, formatNumber } from "@/lib/format";
import { Card, SectionTitle } from "../Card";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import { EmptyState } from "../ui";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

function Stat({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: IconType;
}) {
  return (
    <div className="rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-secondary/50 p-3.5 shadow-sm shadow-black/[0.02]">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-tg-button/10 text-tg-button">
        <Icon className="h-4 w-4" aria-hidden />
      </span>
      <div className="mt-2 text-2xl font-bold leading-none">
        {formatNumber(value)}
      </div>
      <div className="mt-1 text-xs text-tg-hint">{label}</div>
    </div>
  );
}

function RecentUserRow({ user }: { user: RecentUser }) {
  const isPremium = user.tier === "premium";
  const initial = (user.first_name || "?").charAt(0).toUpperCase();
  return (
    <li className="flex items-center gap-3 py-2.5">
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-tg-hint/12 text-xs font-semibold text-tg-text">
        {initial}
      </span>
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-1 truncate text-sm font-medium text-tg-text">
          {user.first_name}
          {isPremium && (
            <Crown className="h-3.5 w-3.5 text-amber-500" aria-hidden />
          )}
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

export function AdminOverview() {
  const { data, error, loading, reload } = useApi<AdminStatsResponse>(() =>
    api.adminStats(),
  );

  if (loading) return <CardSkeleton lines={4} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <Stat label="Users" value={data.users} icon={Users} />
        <Stat label="Premium" value={data.premium} icon={Crown} />
        <Stat
          label="Messages today"
          value={data.messages_today}
          icon={MessageSquare}
        />
        <Stat label="Payments" value={data.payments} icon={CreditCard} />
      </div>

      <Card>
        <SectionTitle icon={Users}>Recent users</SectionTitle>
        {data.recent_users.length === 0 ? (
          <EmptyState icon={Users} title="No users yet" />
        ) : (
          <ul className="-mx-1 divide-y divide-black/[0.05] dark:divide-white/[0.06]">
            {data.recent_users.map((u) => (
              <RecentUserRow key={u.id} user={u} />
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
