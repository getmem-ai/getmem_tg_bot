"use client";

import { useState, type ComponentType } from "react";
import {
  Bot,
  ChevronLeft,
  ChevronRight,
  LayoutGrid,
  Layers,
  Megaphone,
  Server,
  Shield,
  Users,
  Wand2,
} from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { OnboardingState } from "@/lib/types";
import { PageHeader } from "./Card";
import { CardSkeleton } from "./Skeleton";
import { AdminOverview } from "./admin/AdminOverview";
import { RuntimeEditor } from "./admin/RuntimeEditor";
import { ProvidersEditor } from "./admin/ProvidersEditor";
import { TiersEditor } from "./admin/TiersEditor";
import { UsersManager } from "./admin/UsersManager";
import { BroadcastForm } from "./admin/BroadcastForm";
import { TemplatesManager } from "./admin/TemplatesManager";
import { SetupWizard } from "./admin/SetupWizard";
import { PromptEditor } from "./PromptEditor";
import { hapticSelection } from "@/lib/telegram";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
type Section =
  | "overview"
  | "users"
  | "bot"
  | "setup"
  | "broadcast"
  | "providers"
  | "tiers";

interface SectionDef {
  key: Section;
  title: string;
  subtitle: string;
  icon: IconType;
  render: () => React.ReactNode;
}

const SECTIONS: ReadonlyArray<SectionDef> = [
  { key: "overview", title: "Overview", subtitle: "Stats, analytics & recent users", icon: LayoutGrid, render: () => <AdminOverview /> },
  { key: "users", title: "Users", subtitle: "Search, ban, grant plans & admin", icon: Users, render: () => <UsersManager /> },
  {
    key: "bot",
    title: "Bot",
    subtitle: "System prompt, voice, models, kill-switch",
    icon: Bot,
    render: () => (
      <div className="space-y-3">
        <PromptEditor />
        <RuntimeEditor />
      </div>
    ),
  },
  { key: "setup", title: "Setup & templates", subtitle: "Starter presets, backup & restore", icon: Wand2, render: () => <TemplatesManager /> },
  { key: "broadcast", title: "Broadcast", subtitle: "Message all users or a tier", icon: Megaphone, render: () => <BroadcastForm /> },
  { key: "providers", title: "Providers", subtitle: "OpenRouter, OpenAI, Anthropic & more", icon: Server, render: () => <ProvidersEditor /> },
  { key: "tiers", title: "Tiers", subtitle: "Plans, prices & model packages", icon: Layers, render: () => <TiersEditor /> },
];

/** Admin tab — list-menu navigation. Only rendered when current user is_admin. */
export function AdminTab() {
  const [active, setActive] = useState<Section | null>(null);
  const onboarding = useApi<OnboardingState>(() => api.getOnboarding());
  const current = SECTIONS.find((s) => s.key === active);

  // First run: guide the operator through a template before showing the menu.
  if (onboarding.loading && !onboarding.data) {
    return <CardSkeleton lines={5} />;
  }
  if (onboarding.data && !onboarding.data.onboarded) {
    return <SetupWizard onDone={() => onboarding.reload()} />;
  }

  if (current) {
    return (
      <div className="flex flex-col gap-4">
        <button
          type="button"
          onClick={() => {
            hapticSelection();
            setActive(null);
          }}
          className="-ml-1 flex items-center gap-1 self-start rounded-full py-1 pl-1 pr-3 text-sm font-semibold text-primary transition active:bg-primary/10"
        >
          <ChevronLeft className="h-5 w-5" aria-hidden />
          Admin
        </button>
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <current.icon className="h-5 w-5" aria-hidden />
          </span>
          <div>
            <h1 className="text-lg font-bold text-text">{current.title}</h1>
            <p className="text-xs text-muted">{current.subtitle}</p>
          </div>
        </div>
        <div key={active} className="animate-fade-in space-y-3">
          {current.render()}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Admin" subtitle="Manage the bot" icon={Shield} />
      <div className="overflow-hidden rounded-card border border-border bg-surface shadow-card">
        {SECTIONS.map((s, i) => (
          <button
            key={s.key}
            type="button"
            onClick={() => {
              hapticSelection();
              setActive(s.key);
            }}
            className={`flex w-full items-center gap-3 px-4 py-3.5 text-left transition active:bg-surface-2 ${
              i > 0 ? "border-t border-border" : ""
            }`}
          >
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <s.icon className="h-5 w-5" aria-hidden />
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-semibold text-text">{s.title}</span>
              <span className="block truncate text-xs text-muted">{s.subtitle}</span>
            </span>
            <ChevronRight className="h-5 w-5 shrink-0 text-muted" aria-hidden />
          </button>
        ))}
      </div>
    </div>
  );
}
