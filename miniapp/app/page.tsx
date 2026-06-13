"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { hasInitData, initWebApp } from "@/lib/telegram";
import type {
  ActivityResponse,
  MeResponse,
  UsageSeriesResponse,
} from "@/lib/types";

import { OpenInTelegram } from "@/components/OpenInTelegram";
import { ProfileCard } from "@/components/ProfileCard";
import { UsageRing } from "@/components/UsageRing";
import { UsageChart } from "@/components/UsageChart";
import { TotalsCards } from "@/components/TotalsCards";
import { ActivityList } from "@/components/ActivityList";
import { AdminPanel } from "@/components/AdminPanel";
import { CardSkeleton, Skeleton } from "@/components/Skeleton";
import { ErrorState } from "@/components/ErrorState";

const USAGE_DAYS = 14;
const ACTIVITY_LIMIT = 20;

export default function DashboardPage() {
  // `ready` flips once we've decided we're inside Telegram (or have dev data).
  const [ready, setReady] = useState(false);
  const [inside, setInside] = useState(false);
  // Bumped on theme change to re-render theme-dependent (chart) colors.
  const [, setThemeNonce] = useState(0);

  useEffect(() => {
    const cleanup = initWebApp(() => setThemeNonce((n) => n + 1));
    setInside(hasInitData());
    setReady(true);
    return cleanup;
  }, []);

  if (!ready) {
    return <BootSkeleton />;
  }

  if (!inside) {
    return <OpenInTelegram />;
  }

  return <Dashboard />;
}

function Dashboard() {
  const me = useApi<MeResponse>(() => api.me());
  const usage = useApi<UsageSeriesResponse>(() => api.usage(USAGE_DAYS));
  const activity = useApi<ActivityResponse>(() => api.activity(ACTIVITY_LIMIT));

  const reloadAll = () => {
    me.reload();
    usage.reload();
    activity.reload();
  };

  // A hard failure on /me means we can't render the dashboard at all.
  if (me.error && !me.data) {
    return (
      <main className="mx-auto w-full max-w-md px-4 py-6">
        <ErrorState error={me.error} onRetry={reloadAll} />
      </main>
    );
  }

  return (
    <main className="mx-auto flex w-full max-w-md flex-col gap-4 px-4 py-5 pb-10">
      {/* Profile */}
      {me.loading || !me.data ? (
        <CardSkeleton lines={2} />
      ) : (
        <ProfileCard user={me.data.user} />
      )}

      {/* Today's usage */}
      {me.loading || !me.data ? (
        <CardSkeleton lines={2} />
      ) : (
        <UsageRing usage={me.data.usage} />
      )}

      {/* Usage chart */}
      {usage.loading ? (
        <CardSkeleton lines={4} />
      ) : usage.error ? (
        <ErrorState error={usage.error} onRetry={usage.reload} />
      ) : usage.data ? (
        <UsageChart series={usage.data.series} />
      ) : null}

      {/* Totals */}
      {me.loading || !me.data ? (
        <div className="flex gap-3">
          <Skeleton className="h-[88px] flex-1 rounded-card" />
          <Skeleton className="h-[88px] flex-1 rounded-card" />
        </div>
      ) : (
        <TotalsCards totals={me.data.totals} />
      )}

      {/* Recent activity */}
      {activity.loading ? (
        <CardSkeleton lines={4} />
      ) : activity.error ? (
        <ErrorState error={activity.error} onRetry={activity.reload} />
      ) : activity.data ? (
        <ActivityList items={activity.data.items} />
      ) : null}

      {/* Admin (only fetched + rendered for admins) */}
      {me.data?.is_admin && <AdminPanel />}

      <footer className="pt-2 text-center text-xs text-tg-hint">
        Powered by GetMem
      </footer>
    </main>
  );
}

function BootSkeleton() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-col gap-4 px-4 py-5">
      <CardSkeleton lines={2} />
      <CardSkeleton lines={2} />
      <CardSkeleton lines={4} />
    </main>
  );
}
