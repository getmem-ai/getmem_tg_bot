"use client";

import type { ReactNode } from "react";
import { Settings } from "lucide-react";
import type { MeResponse } from "@/lib/types";
import { PageHeader } from "./Card";
import { ModelPicker } from "./ModelPicker";
import { RoleEditor } from "./RoleEditor";
import { UpgradeCard } from "./UpgradeCard";

interface SettingsTabProps {
  me: MeResponse;
  onModelChange?: (model: string | null) => void;
  onReload?: () => void;
}

/** A labelled group: short uppercase title, optional subtitle, then content. */
function Section({
  label,
  subtitle,
  children,
}: {
  label: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-2">
      <div className="px-1">
        <h2 className="text-[0.7rem] font-semibold uppercase tracking-wider text-tg-hint">
          {label}
        </h2>
        {subtitle && (
          <p className="mt-0.5 text-xs text-tg-hint/80">{subtitle}</p>
        )}
      </div>
      {children}
    </section>
  );
}

export function SettingsTab({ me, onModelChange, onReload }: SettingsTabProps) {
  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Settings"
        subtitle="Personalize your assistant"
        icon={Settings}
      />

      {me.user_roles_enabled && (
        <Section
          label="Persona"
          subtitle="Tell the assistant how to behave in your chats"
        >
          <RoleEditor
            role={me.user.role}
            enabled={me.user.role_enabled}
            onSaved={onReload}
          />
        </Section>
      )}

      <Section label="AI model" subtitle="Choose which model answers you">
        <ModelPicker
          available={me.available_models}
          current={me.user.preferred_model}
          onChange={onModelChange}
        />
      </Section>

      <Section label="Upgrade" subtitle="Unlock higher limits and more models">
        <UpgradeCard tiers={me.upgrade_tiers} onPaid={onReload} />
      </Section>
    </div>
  );
}
