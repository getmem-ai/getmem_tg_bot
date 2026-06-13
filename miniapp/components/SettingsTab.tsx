"use client";

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

export function SettingsTab({ me, onModelChange, onReload }: SettingsTabProps) {
  return (
    <div className="flex flex-col gap-4">
      <PageHeader
        title="Settings"
        subtitle="Personalize your assistant"
        icon={Settings}
      />

      {me.user_roles_enabled && (
        <RoleEditor role={me.user.role} onSaved={onReload} />
      )}

      <ModelPicker
        available={me.available_models}
        current={me.user.preferred_model}
        onChange={onModelChange}
      />

      <UpgradeCard tiers={me.upgrade_tiers} onPaid={onReload} />
    </div>
  );
}
