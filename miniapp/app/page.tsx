"use client";

import { useEffect, useMemo, useState } from "react";
import { Clock, LayoutDashboard, Settings, Shield } from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { hasInitData, initWebApp } from "@/lib/telegram";
import type {
  ActivityResponse,
  MeResponse,
  UsageSeriesResponse,
} from "@/lib/types";

import { OpenInTelegram } from "@/components/OpenInTelegram";
import { PageHeader } from "@/components/Card";
import { ProfileCard } from "@/components/ProfileCard";
import { UsageRing } from "@/components/UsageRing";
import { UsageChart } from "@/components/UsageChart";
import { TotalsCards } from "@/components/TotalsCards";
import { ActivityList } from "@/components/ActivityList";
import { SettingsTab } from "@/components/SettingsTab";
import { AdminTab } from "@/components/AdminTab";
import { CardSkeleton, Skeleton } from "@/components/Skeleton";
import { ErrorState } from "@/components/ErrorState";
import { TabBar, type TabDef, type TabKey } from "@/components/TabBar";

const USAGE_DAYS = 14;
const ACTIVITY_LIMIT = 20;

export default function App() {
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

  if (!ready) return <BootSkeleton />;
  if (!inside) return <OpenInTelegram />;
  return <Shell />;
}

function Shell() {
  const me = useApi<MeResponse>(() => api.me());
  const [tab, setTab] = useState<TabKey>("home");

  const isAdmin = me.data?.is_admin ?? false;

  const tabs = useMemo<TabDef[]>(() => {
    const base: TabDef[] = [
      { key: "home", label: "Home", icon: LayoutDashboard },
      { key: "activity", label: "Activity", icon: Clock },
      { key: "settings", label: "Settings", icon: Settings },
    ];
    if (isAdmin) base.push({ key: "admin", label: "Admin", icon: Shield });
    return base;
  }, [isAdmin]);

  // If the active tab disappears (e.g. admin flag resolves false), fall back.
  useEffect(() => {
    if (!tabs.some((t) => t.key === tab)) setTab("home");
  }, [tabs, tab]);

  // A hard failure on /me means we can't render anything meaningful.
  if (me.error && !me.data) {
    return (
      <main className="mx-auto w-full max-w-md px-4 py-6">
        <ErrorState error={me.error} onRetry={me.reload} />
      </main>
    );
  }

  return (
    <>
      <main className="mx-auto w-full max-w-md px-4 pt-5 pb-tabbar">
        <div key={tab} className="animate-fade-in">
          {tab === "home" && <HomeTab me={me} />}
          {tab === "activity" && <ActivityTab />}
          {tab === "settings" && <SettingsTabView me={me} />}
          {tab === "admin" && isAdmin && <AdminTab />}
        </div>

        <footer className="pt-6 pb-2 text-center text-xs text-tg-hint">
          Powered by GetMem
        </footer>
      </main>

      <TabBar tabs={tabs} active={tab} onChange={setTab} />
    </>
  );
}

// ---------------------------------------------------------------------------
// Home
// ---------------------------------------------------------------------------

function HomeTab({ me }: { me: ReturnType<typeof useApi<MeResponse>> }) {
  const usage = useApi<UsageSeriesResponse>(() => api.usage(USAGE_DAYS));

  return (
    <div className="flex flex-col gap-4">
      {me.loading || !me.data ? (
        <>
          <CardSkeleton lines={2} />
          <CardSkeleton lines={2} />
        </>
      ) : (
        <>
          <ProfileCard user={me.data.user} tier={me.data.tier} />
          <UsageRing usage={me.data.usage} />
        </>
      )}

      {usage.loading ? (
        <CardSkeleton lines={4} />
      ) : usage.error ? (
        <ErrorState error={usage.error} onRetry={usage.reload} />
      ) : usage.data ? (
        <UsageChart series={usage.data.series} />
      ) : null}

      {me.loading || !me.data ? (
        <div className="flex gap-3">
          <Skeleton className="h-[104px] flex-1 rounded-2xl" />
          <Skeleton className="h-[104px] flex-1 rounded-2xl" />
        </div>
      ) : (
        <TotalsCards totals={me.data.totals} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Activity
// ---------------------------------------------------------------------------

function ActivityTab() {
  const activity = useApi<ActivityResponse>(() => api.activity(ACTIVITY_LIMIT));

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Activity" subtitle="Your recent messages" icon={Clock} />
      {activity.loading ? (
        <CardSkeleton lines={5} />
      ) : activity.error ? (
        <ErrorState error={activity.error} onRetry={activity.reload} />
      ) : activity.data ? (
        <ActivityList items={activity.data.items} />
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

function SettingsTabView({ me }: { me: ReturnType<typeof useApi<MeResponse>> }) {
  if (me.loading || !me.data) {
    return (
      <div className="flex flex-col gap-4">
        <CardSkeleton lines={5} />
      </div>
    );
  }
  return <SettingsTab me={me.data} onModelChange={() => me.reload()} />;
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
