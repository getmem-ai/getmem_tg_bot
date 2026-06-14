"use client";

import { useState } from "react";
import { Check, KeyRound, Layers, Rocket, X } from "lucide-react";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { ConfigApplyResult, OnboardingState } from "@/lib/types";
import { Card } from "../Card";
import { Button } from "../ui";
import { TemplateGallery } from "./TemplateGallery";

function ChecklistRow({
  ok,
  icon: Icon,
  label,
  hint,
}: {
  ok: boolean;
  icon: typeof KeyRound;
  label: string;
  hint: string;
}) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
      <span
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
          ok ? "bg-green-500/15 text-green-600" : "bg-primary/10 text-primary"
        }`}
      >
        {ok ? <Check className="h-4 w-4" aria-hidden /> : <Icon className="h-4 w-4" aria-hidden />}
      </span>
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text">{label}</p>
        <p className="text-xs text-muted">{hint}</p>
      </div>
    </div>
  );
}

/** First-run guided setup: pick a template, then confirm the essentials. */
export function SetupWizard({ onDone }: { onDone: () => void }) {
  const onboarding = useApi<OnboardingState>(() => api.getOnboarding());
  const [step, setStep] = useState<"pick" | "done">("pick");
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [applied, setApplied] = useState<ConfigApplyResult | null>(null);
  const [finishing, setFinishing] = useState(false);
  const [error, setError] = useState("");

  async function apply(key: string) {
    setBusyKey(key);
    setError("");
    try {
      setApplied(await api.applyTemplate(key));
      onboarding.reload();
      setStep("done");
    } catch {
      setError("Couldn't apply that template. Try again.");
    } finally {
      setBusyKey(null);
    }
  }

  async function finish() {
    setFinishing(true);
    setError("");
    try {
      await api.completeOnboarding();
      onDone();
    } catch {
      setError("Couldn't finish setup.");
      setFinishing(false);
    }
  }

  if (step === "pick") {
    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-xl font-bold text-text">Welcome 👋</h1>
            <p className="text-sm text-muted">
              Pick a starting point for your bot. You can fine-tune everything
              afterwards.
            </p>
          </div>
          <button
            type="button"
            onClick={finish}
            className="shrink-0 rounded-full p-1 text-muted transition active:bg-surface-2"
            aria-label="Skip setup"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>
        <Card>
          <TemplateGallery onApply={apply} busyKey={busyKey} />
        </Card>
        {error && <p className="px-1 text-xs text-red-500">{error}</p>}
        <button
          type="button"
          onClick={finish}
          className="self-center text-xs font-medium text-muted underline-offset-2 active:underline"
        >
          Skip — I'll configure it manually
        </button>
      </div>
    );
  }

  const ob = onboarding.data;
  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-xl font-bold text-text">Almost there 🎉</h1>
        <p className="text-sm text-muted">
          {applied && applied.applied.length > 0
            ? `Applied: ${applied.applied.join(", ")}.`
            : "Template applied."}
        </p>
      </div>

      <div className="space-y-2">
        <ChecklistRow
          ok={!!ob?.has_openrouter_key}
          icon={KeyRound}
          label="LLM provider key"
          hint={
            ob?.has_openrouter_key
              ? "OpenRouter key detected — your bot can reply out of the box."
              : "Add OPENROUTER_API_KEY (or a provider key in Providers) so the bot can reply."
          }
        />
        <ChecklistRow
          ok={(ob?.providers_configured ?? 0) > 0}
          icon={KeyRound}
          label="Providers configured"
          hint={`${ob?.providers_configured ?? 0} provider(s) ready. Add more keys in the Providers section.`}
        />
        <ChecklistRow
          ok={(ob?.tiers_count ?? 0) > 0}
          icon={Layers}
          label="Plans & limits"
          hint={`${ob?.tiers_count ?? 0} tier(s) set. Tune prices and limits in the Tiers section.`}
        />
      </div>

      {applied && applied.todo.length > 0 && (
        <Card>
          <p className="text-sm font-semibold text-text">A couple of things to finish:</p>
          <ul className="mt-2 list-disc pl-5 text-xs text-muted">
            {applied.todo.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </Card>
      )}

      {error && <p className="px-1 text-xs text-red-500">{error}</p>}

      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => setStep("pick")}
          className="text-xs font-medium text-muted active:underline"
        >
          ← Pick a different template
        </button>
        <Button onClick={finish} disabled={finishing} icon={Rocket} size="sm">
          {finishing ? "Finishing…" : "Go to dashboard"}
        </Button>
      </div>
    </div>
  );
}
