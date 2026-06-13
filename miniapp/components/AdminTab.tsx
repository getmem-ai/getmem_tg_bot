"use client";

import { useState } from "react";
import {
  Bot,
  LayoutGrid,
  Layers,
  Megaphone,
  Server,
  Shield,
  Users,
} from "lucide-react";
import { PageHeader } from "./Card";
import { SegmentedControl, type SegmentOption } from "./ui";
import { AdminOverview } from "./admin/AdminOverview";
import { RuntimeEditor } from "./admin/RuntimeEditor";
import { ProvidersEditor } from "./admin/ProvidersEditor";
import { TiersEditor } from "./admin/TiersEditor";
import { UsersManager } from "./admin/UsersManager";
import { BroadcastForm } from "./admin/BroadcastForm";
import { PromptEditor } from "./PromptEditor";

type Section =
  | "overview"
  | "users"
  | "bot"
  | "broadcast"
  | "providers"
  | "tiers";

const SECTIONS: ReadonlyArray<SegmentOption<Section>> = [
  { value: "overview", label: "Overview", icon: LayoutGrid },
  { value: "users", label: "Users", icon: Users },
  { value: "bot", label: "Bot", icon: Bot },
  { value: "broadcast", label: "Broadcast", icon: Megaphone },
  { value: "providers", label: "Providers", icon: Server },
  { value: "tiers", label: "Tiers", icon: Layers },
];

/** Admin tab — only rendered when the current user is_admin. */
export function AdminTab() {
  const [section, setSection] = useState<Section>("overview");

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Admin" subtitle="Manage the bot" icon={Shield} />

      <SegmentedControl
        options={SECTIONS}
        value={section}
        onChange={setSection}
        scroll
      />

      <div key={section} className="animate-fade-in space-y-3">
        {section === "overview" && <AdminOverview />}
        {section === "users" && <UsersManager />}
        {section === "bot" && (
          <>
            <PromptEditor />
            <RuntimeEditor />
          </>
        )}
        {section === "broadcast" && <BroadcastForm />}
        {section === "providers" && <ProvidersEditor />}
        {section === "tiers" && <TiersEditor />}
      </div>
    </div>
  );
}
