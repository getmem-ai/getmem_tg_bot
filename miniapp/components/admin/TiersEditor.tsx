"use client";

import { useMemo, useState } from "react";
import { Check, Layers, Save } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type {
  ModelSpec,
  Provider,
  ProvidersResponse,
  TierConfig,
  TiersResponse,
} from "@/lib/types";
import { Card } from "../Card";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import { Button, SaveMessage, type SaveStatus } from "../ui";

const PROVIDER_LABEL: Record<string, string> = {
  openrouter: "OpenRouter",
  openai: "OpenAI",
  anthropic: "Anthropic",
};

interface DraftTier {
  key: string;
  name: string;
  daily_limit: number;
  selected: Set<string>; // model ids
}

export function TiersEditor() {
  const tiers = useApi<TiersResponse>(() => api.getTiers());
  const providers = useApi<ProvidersResponse>(() => api.getProviders());

  const loading = tiers.loading || providers.loading;
  const error = tiers.error ?? providers.error;

  // Union of models offered by enabled providers — the pool a tier can grant.
  const modelPool: ModelSpec[] = useMemo(() => {
    const pool: ModelSpec[] = [];
    const seen = new Set<string>();
    for (const p of providers.data?.providers ?? []) {
      if (!p.enabled) continue;
      for (const id of p.models) {
        if (seen.has(id)) continue;
        seen.add(id);
        pool.push({ provider: p.kind, id, label: id.split("/").pop() ?? id });
      }
    }
    // Also include any model already assigned to a tier (so nothing disappears).
    for (const t of tiers.data?.tiers ?? []) {
      for (const m of t.models) {
        if (seen.has(m.id)) continue;
        seen.add(m.id);
        pool.push(m);
      }
    }
    return pool;
  }, [providers.data, tiers.data]);

  if (loading) return <CardSkeleton lines={6} />;
  if (error)
    return (
      <ErrorState
        error={error}
        onRetry={() => {
          tiers.reload();
          providers.reload();
        }}
      />
    );
  if (!tiers.data) return null;

  return (
    <div className="space-y-3">
      {tiers.data.tiers.map((t) => (
        <TierRow key={t.key} tier={t} pool={modelPool} />
      ))}
    </div>
  );
}

function TierRow({ tier, pool }: { tier: TierConfig; pool: ModelSpec[] }) {
  const [draft, setDraft] = useState<DraftTier>(() => ({
    key: tier.key,
    name: tier.name,
    daily_limit: tier.daily_limit,
    selected: new Set(tier.models.map((m) => m.id)),
  }));
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  function toggleModel(id: string) {
    setDraft((d) => {
      const next = new Set(d.selected);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { ...d, selected: next };
    });
  }

  async function save() {
    setStatus("saving");
    setMessage("");
    const models = pool
      .filter((m) => draft.selected.has(m.id))
      .map((m) => ({ provider: m.provider as Provider, id: m.id }));
    try {
      await api.setTiers([
        { key: draft.key, daily_limit: draft.daily_limit, models },
      ]);
      setStatus("saved");
      setMessage("Saved");
      window.setTimeout(() => setStatus("idle"), 2000);
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.isForbidden
          ? "Admins only."
          : "Failed to save.",
      );
    }
  }

  return (
    <Card>
      <div className="mb-3 flex items-center gap-2.5">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-tg-button/10 text-tg-button">
          <Layers className="h-5 w-5" aria-hidden />
        </span>
        <p className="flex-1 text-sm font-semibold">{tier.name}</p>
        <span className="text-xs text-tg-hint">{draft.selected.size} models</span>
      </div>

      <label className="mb-1 block text-xs font-medium text-tg-hint">
        Daily message limit
      </label>
      <input
        type="number"
        inputMode="numeric"
        min={0}
        value={Number.isFinite(draft.daily_limit) ? draft.daily_limit : 0}
        onChange={(e) =>
          setDraft((d) => ({
            ...d,
            daily_limit: Math.max(0, Number(e.target.value) || 0),
          }))
        }
        className="w-32 rounded-xl border border-black/[0.1] dark:border-white/[0.12] bg-tg-bg/60 px-3 py-2 text-sm text-tg-text outline-none transition focus:border-tg-button"
      />

      <label className="mb-2 mt-3 block text-xs font-medium text-tg-hint">
        Models available to this tier
      </label>
      {pool.length === 0 ? (
        <p className="text-xs text-tg-hint">
          No models available. Enable a provider and add models first.
        </p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {pool.map((m) => {
            const on = draft.selected.has(m.id);
            return (
              <button
                key={m.id}
                onClick={() => toggleModel(m.id)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition ${
                  on
                    ? "border-tg-button/40 bg-tg-button/12 text-tg-button"
                    : "border-black/[0.08] dark:border-white/[0.12] text-tg-hint active:bg-black/[0.04] dark:active:bg-white/[0.06]"
                }`}
                title={m.id}
              >
                {on && <Check className="h-3 w-3" aria-hidden />}
                <span className="max-w-[10rem] truncate">{m.label}</span>
                <span className="opacity-50">
                  {PROVIDER_LABEL[m.provider]?.[0] ?? ""}
                </span>
              </button>
            );
          })}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between gap-3">
        <SaveMessage status={status} message={message} />
        <Button
          onClick={save}
          disabled={status === "saving"}
          icon={Save}
          size="sm"
        >
          {status === "saving" ? "Saving…" : "Save"}
        </Button>
      </div>
    </Card>
  );
}
