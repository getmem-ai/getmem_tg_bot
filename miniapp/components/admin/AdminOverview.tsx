"use client";

import type { ComponentType } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  BarChart3,
  Crown,
  CreditCard,
  Cpu,
  MessageSquare,
  Sparkles,
  UserPlus,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type {
  AdminStatsResponse,
  AnalyticsResponse,
  DayCount,
  RecentUser,
} from "@/lib/types";
import { formatDate, formatNumber, shortDay, shortModel } from "@/lib/format";
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
    <div className="rounded-card border border-black/[0.04] dark:border-white/[0.06] bg-tg-bg p-4 shadow-card">
      <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
        <Icon className="h-5 w-5" aria-hidden />
      </span>
      <div className="mt-3 text-2xl font-bold leading-none tabular-nums">
        {formatNumber(value)}
      </div>
      <div className="mt-1.5 text-xs text-tg-hint">{label}</div>
    </div>
  );
}

function RecentUserRow({ user }: { user: RecentUser }) {
  const isPremium = user.tier === "premium";
  const initial = (user.first_name || "?").charAt(0).toUpperCase();
  return (
    <li className="flex items-center gap-3 py-2.5">
      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-brand/10 text-sm font-semibold text-brand">
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

interface DayTooltipItem {
  value: number;
  payload: DayCount & { label: string };
}

function DayTooltip({
  active,
  payload,
  unit,
}: {
  active?: boolean;
  payload?: DayTooltipItem[];
  unit: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const point = payload[0].payload;
  return (
    <div className="rounded-xl border border-black/[0.06] bg-tg-bg px-3 py-2 text-xs shadow-card dark:border-white/[0.08]">
      <div className="font-semibold text-tg-text">{shortDay(point.day)}</div>
      <div className="text-tg-hint">
        {point.count} {unit}
      </div>
    </div>
  );
}

const CHART_MARGIN = { top: 6, right: 6, left: -22, bottom: 0 } as const;
const AXIS_TICK = { fontSize: 10, fill: "var(--tg-hint)" } as const;

function MessagesChart({ series }: { series: DayCount[] }) {
  const data = series.map((p) => ({ ...p, label: shortDay(p.day) }));
  const total = series.reduce((sum, p) => sum + p.count, 0);

  if (total === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-tg-hint">
        No messages yet
      </div>
    );
  }

  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={CHART_MARGIN}>
          <defs>
            <linearGradient id="analyticsMsgFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--brand)" stopOpacity={0.45} />
              <stop offset="100%" stopColor="var(--brand)" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--tg-hint)"
            strokeOpacity={0.12}
            vertical={false}
          />
          <XAxis
            dataKey="label"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
            minTickGap={16}
          />
          <YAxis
            allowDecimals={false}
            width={28}
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            content={<DayTooltip unit="messages" />}
            cursor={{ stroke: "var(--tg-hint)", strokeOpacity: 0.2 }}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke="var(--brand)"
            strokeWidth={2.5}
            fill="url(#analyticsMsgFill)"
            dot={false}
            activeDot={{
              r: 4,
              fill: "var(--brand)",
              stroke: "var(--tg-bg)",
              strokeWidth: 2,
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function NewUsersChart({ series }: { series: DayCount[] }) {
  const data = series.map((p) => ({ ...p, label: shortDay(p.day) }));
  const total = series.reduce((sum, p) => sum + p.count, 0);

  if (total === 0) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-tg-hint">
        No new users yet
      </div>
    );
  }

  return (
    <div className="h-40 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={CHART_MARGIN}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="var(--tg-hint)"
            strokeOpacity={0.12}
            vertical={false}
          />
          <XAxis
            dataKey="label"
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
            minTickGap={16}
          />
          <YAxis
            allowDecimals={false}
            width={28}
            tick={AXIS_TICK}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            content={<DayTooltip unit="new users" />}
            cursor={{ fill: "var(--tg-hint)", fillOpacity: 0.08 }}
          />
          <Bar dataKey="count" fill="var(--brand)" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function ModelMix({ models }: { models: AnalyticsResponse["model_mix"] }) {
  if (models.length === 0) {
    return <EmptyState icon={Cpu} title="No model usage yet" />;
  }
  const max = Math.max(...models.map((m) => m.count), 1);
  return (
    <ul className="space-y-2">
      {models.map((m) => (
        <li key={m.model}>
          <div className="mb-1 flex items-center justify-between gap-2 text-xs">
            <span className="truncate text-tg-text">{shortModel(m.model)}</span>
            <span className="shrink-0 tabular-nums text-tg-hint">
              {formatNumber(m.count)}
            </span>
          </div>
          <div className="h-2 w-full overflow-hidden rounded-full bg-tg-hint/15">
            <div
              className="h-full rounded-full bg-brand"
              style={{ width: `${(m.count / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

/** Lazily-fetched 14-day analytics shown below the Overview stats. */
function AnalyticsBlock() {
  const { data, error, loading, reload } = useApi<AnalyticsResponse>(() =>
    api.getAnalytics(14),
  );

  if (loading) return <CardSkeleton lines={5} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <>
      <div className="rounded-card border border-black/[0.04] dark:border-white/[0.06] bg-tg-bg p-4 shadow-card">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-500">
          <Sparkles className="h-5 w-5" aria-hidden />
        </span>
        <div className="mt-3 text-2xl font-bold leading-none tabular-nums">
          ⭐ {formatNumber(data.revenue_stars)} Stars
        </div>
        <div className="mt-1.5 text-xs text-tg-hint">Earned (last 14 days)</div>
      </div>

      <Card>
        <SectionTitle icon={BarChart3}>Messages / day</SectionTitle>
        <MessagesChart series={data.messages} />
      </Card>

      <Card>
        <SectionTitle icon={UserPlus}>New users / day</SectionTitle>
        <NewUsersChart series={data.new_users} />
      </Card>

      <Card>
        <SectionTitle icon={Cpu}>Model mix</SectionTitle>
        <ModelMix models={data.model_mix} />
      </Card>
    </>
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

      <AnalyticsBlock />
    </div>
  );
}
