"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlarmClock,
  ArrowRight,
  Clock,
  LayoutDashboard,
  Moon,
  Settings,
  Shield,
  Sun,
  Sunrise,
  Sunset,
} from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { hasInitData, initWebApp } from "@/lib/telegram";
import { nextOccurrences, timeChip, dayLabel, timeOfDay } from "@/lib/schedule";
import type {
  ActivityResponse,
  MeResponse,
  SchedulesResponse,
  UsageSeriesResponse,
} from "@/lib/types";
import { OpenInTelegram } from "@/components/OpenInTelegram";
import { AppHeader } from "@/components/AppHeader";
import { PageHeader, SectionTitle } from "@/components/Card";
import { ProfileCard } from "@/components/ProfileCard";
import { UsageRing } from "@/components/UsageRing";
import { UsageChart } from "@/components/UsageChart";
import { TotalsCards } from "@/components/TotalsCards";
import { ActivityList } from "@/components/ActivityList";
import { SchedulesTab } from "@/components/SchedulesTab";
import { SettingsTab } from "@/components/SettingsTab";
import { AdminTab } from "@/components/AdminTab";
import { CardSkeleton, Skeleton } from "@/components/Skeleton";
import { ErrorState } from "@/components/ErrorState";
import { TabBar, type TabDef, type TabKey } from "@/components/TabBar";

const USAGE_DAYS = 14;
const ACTIVITY_LIMIT = 15;

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
      { key: "schedules", label: "Schedules", icon: AlarmClock },
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
        <AppHeader name={me.data?.brand?.name} tagline={me.data?.brand?.tagline} />
        <div key={tab} className="animate-fade-in">
          {tab === "home" && (
            <HomeTab
              me={me}
              onUpgrade={() => setTab("settings")}
              onOpenSchedules={() => setTab("schedules")}
            />
          )}
          {tab === "activity" && <ActivityTab />}
          {tab === "schedules" && <SchedulesTab />}
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

function HomeTab({
  me,
  onUpgrade,
  onOpenSchedules,
}: {
  me: ReturnType<typeof useApi<MeResponse>>;
  onUpgrade?: () => void;
  onOpenSchedules?: () => void;
}) {
  const usage = useApi<UsageSeriesResponse>(() => api.usage(USAGE_DAYS));
  // Only offer upgrade when there's actually a paid plan configured.
  const canUpgrade = (me.data?.upgrade_tiers?.length ?? 0) > 0;

  return (
    <div className="flex flex-col gap-3">
      {me.loading || !me.data ? (
        <>
          <CardSkeleton lines={2} />
          <CardSkeleton lines={2} />
        </>
      ) : (
        <>
          <ProfileCard
            user={me.data.user}
            tier={me.data.tier}
            onUpgrade={canUpgrade ? onUpgrade : undefined}
            onProfileSaved={() => me.reload()}
          />
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

      <UpcomingSection onOpenSchedules={onOpenSchedules} />

      {me.loading || !me.data ? (
        <div className="flex gap-3">
          <Skeleton className="h-[118px] flex-1 rounded-card" />
          <Skeleton className="h-[118px] flex-1 rounded-card" />
        </div>
      ) : (
        <TotalsCards totals={me.data.totals} />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Home → Upcoming reminders (horizontal snap-scroll)
// ---------------------------------------------------------------------------

const UPCOMING_COUNT = 6;

const UPCOMING_ICON = {
  morning: Sunrise,
  noon: Sun,
  evening: Sunset,
  night: Moon,
} as const;

function UpcomingSection({ onOpenSchedules }: { onOpenSchedules?: () => void }) {
  const schedules = useApi<SchedulesResponse>(() => api.getSchedules());

  const items = useMemo(() => {
    if (!schedules.data || !schedules.data.enabled) return [];
    return nextOccurrences(schedules.data.tasks, UPCOMING_COUNT);
  }, [schedules.data]);

  // Render nothing while loading, on error, or when there are no upcoming runs.
  if (schedules.loading || schedules.error || items.length === 0) return null;

  return (
    <section className="rounded-card border border-black/[0.04] bg-tg-bg p-5 shadow-card dark:border-white/[0.06]">
      <SectionTitle
        icon={AlarmClock}
        right={
          onOpenSchedules && (
            <button
              type="button"
              onClick={onOpenSchedules}
              className="flex items-center gap-0.5 text-xs font-semibold text-primary"
            >
              All
              <ArrowRight className="h-3.5 w-3.5" aria-hidden />
            </button>
          )
        }
      >
        Upcoming
      </SectionTitle>
      <div className="no-scrollbar -mx-1 flex snap-x gap-2.5 overflow-x-auto px-1 [-webkit-overflow-scrolling:touch]">
        {items.map((occ, i) => {
          const hh = `${String(occ.when.getHours()).padStart(2, "0")}:${String(
            occ.when.getMinutes(),
          ).padStart(2, "0")}`;
          const Icon = UPCOMING_ICON[timeOfDay(hh).key];
          return (
            <div
              key={`${occ.task.id}-${i}`}
              className="flex w-40 shrink-0 snap-start flex-col gap-2 rounded-2xl border border-border bg-surface-2/50 p-3.5"
            >
              <div className="flex items-center justify-between">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="h-4 w-4" aria-hidden />
                </span>
                <span className="rounded-full bg-accent/15 px-2 py-0.5 text-[11px] font-semibold text-accent-600">
                  {dayLabel(occ.when)}
                </span>
              </div>
              <p className="truncate text-sm font-semibold text-text">
                {occ.task.title}
              </p>
              <p className="text-xs font-medium text-muted">{timeChip(hh)}</p>
            </div>
          );
        })}
      </div>
    </section>
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
  return (
    <SettingsTab
      me={me.data}
      onModelChange={() => me.reload()}
      onReload={() => me.reload()}
    />
  );
}

function BootSkeleton() {
  return (
    <main className="mx-auto flex w-full max-w-md flex-col gap-4 px-4 py-5">
      <AppHeader />
      <CardSkeleton lines={2} />
      <CardSkeleton lines={2} />
      <CardSkeleton lines={4} />
    </main>
  );
}
