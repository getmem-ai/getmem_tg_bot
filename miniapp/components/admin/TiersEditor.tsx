"use client";

import { useMemo, useState } from "react";
import {
  Check,
  Coins,
  Crown,
  Layers,
  Plus,
  Save,
  Trash2,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type {
  ModelSpec,
  Provider,
  ProvidersResponse,
  TierConfig,
  TiersResponse,
  TierUpdate,
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
  price_stars: number;
  period_days: number;
  selected: Set<string>; // model ids
  isNew: boolean;
}

/** "Pro Plus" -> "pro_plus". Falls back to "tier" when empty. */
function slugify(name: string): string {
  const slug = name
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
  return slug || "tier";
}

function uniqueKey(base: string, taken: Set<string>): string {
  if (!taken.has(base)) return base;
  let i = 2;
  while (taken.has(`${base}_${i}`)) i += 1;
  return `${base}_${i}`;
}

function toDraft(t: TierConfig): DraftTier {
  return {
    key: t.key,
    name: t.name,
    daily_limit: t.daily_limit,
    price_stars: t.price_stars,
    period_days: t.period_days,
    selected: new Set(t.models.map((m) => m.id)),
    isNew: false,
  };
}

export function TiersEditor() {
  const tiers = useApi<TiersResponse>(() => api.getTiers());
  const providers = useApi<ProvidersResponse>(() => api.getProviders());

  const loading = tiers.loading || providers.loading;
  const error = tiers.error ?? providers.error;

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
  if (!tiers.data || !providers.data) return null;

  return (
    <TiersForm
      initial={tiers.data.tiers}
      providers={providers.data}
      onSaved={() => tiers.reload()}
    />
  );
}

function TiersForm({
  initial,
  providers,
  onSaved,
}: {
  initial: TierConfig[];
  providers: ProvidersResponse;
  onSaved: () => void;
}) {
  const [drafts, setDrafts] = useState<DraftTier[]>(() => initial.map(toDraft));
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  // Union of models from enabled providers, plus any already assigned to a tier
  // (so existing selections never silently vanish).
  const modelPool: ModelSpec[] = useMemo(() => {
    const pool: ModelSpec[] = [];
    const seen = new Set<string>();
    for (const p of providers.providers) {
      if (!p.enabled) continue;
      for (const id of p.models) {
        if (seen.has(id)) continue;
        seen.add(id);
        pool.push({ provider: p.kind, id, label: id.split("/").pop() ?? id });
      }
    }
    for (const t of initial) {
      for (const m of t.models) {
        if (seen.has(m.id)) continue;
        seen.add(m.id);
        pool.push(m);
      }
    }
    return pool;
  }, [providers, initial]);

  function update(key: string, patch: Partial<DraftTier>) {
    setDrafts((ds) =>
      ds.map((d) => (d.key === key ? { ...d, ...patch } : d)),
    );
    setStatus("idle");
    setMessage("");
  }

  function toggleModel(key: string, id: string) {
    setDrafts((ds) =>
      ds.map((d) => {
        if (d.key !== key) return d;
        const next = new Set(d.selected);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return { ...d, selected: next };
      }),
    );
    setStatus("idle");
    setMessage("");
  }

  function addTier() {
    setDrafts((ds) => {
      const taken = new Set(ds.map((d) => d.key));
      const key = uniqueKey("custom_tier", taken);
      const next: DraftTier = {
        key,
        name: "New tier",
        daily_limit: 200,
        price_stars: 100,
        period_days: 30,
        selected: new Set(),
        isNew: true,
      };
      return [...ds, next];
    });
    setStatus("idle");
    setMessage("");
  }

  function removeTier(key: string) {
    setDrafts((ds) => ds.filter((d) => d.key !== key));
    setStatus("idle");
    setMessage("");
  }

  async function save() {
    setStatus("saving");
    setMessage("");

    // Finalise keys for new tiers from their name, ensuring uniqueness.
    const taken = new Set<string>();
    const payload: TierUpdate[] = drafts.map((d) => {
      const isFree = d.key === "free";
      const key = d.isNew
        ? uniqueKey(slugify(d.name), taken)
        : d.key;
      taken.add(key);
      const models = modelPool
        .filter((m) => d.selected.has(m.id))
        .map((m) => ({ provider: m.provider as Provider, id: m.id }));
      return {
        key,
        name: d.name.trim() || key,
        daily_limit: d.daily_limit,
        price_stars: isFree ? 0 : d.price_stars,
        period_days: isFree ? 0 : d.period_days,
        models,
      };
    });

    try {
      const res = await api.setTiers(payload);
      // Re-seed drafts from the authoritative response (keys now final).
      setDrafts(res.tiers.map(toDraft));
      setStatus("saved");
      setMessage("Saved");
      onSaved();
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
    <div className="space-y-3">
      <p className="px-1 text-xs text-tg-hint">
        Paid tiers appear in the bot&rsquo;s /upgrade. Free is always available.
      </p>

      {drafts.map((d) => (
        <TierCard
          key={d.key}
          draft={d}
          pool={modelPool}
          onChange={(patch) => update(d.key, patch)}
          onToggleModel={(id) => toggleModel(d.key, id)}
          onDelete={() => removeTier(d.key)}
        />
      ))}

      <button
        type="button"
        onClick={addTier}
        className="flex w-full items-center justify-center gap-2 rounded-2xl border border-dashed border-black/[0.14] py-3 text-sm font-medium text-tg-hint transition active:bg-black/[0.04] dark:border-white/[0.16] dark:active:bg-white/[0.06]"
      >
        <Plus className="h-4 w-4" aria-hidden />
        Add tier
      </button>

      <Card>
        <div className="flex items-center justify-between gap-3">
          <SaveMessage status={status} message={message} />
          <Button
            onClick={save}
            disabled={status === "saving"}
            icon={Save}
            size="sm"
          >
            {status === "saving" ? "Saving…" : "Save tiers"}
          </Button>
        </div>
      </Card>
    </div>
  );
}

const numberFieldClass =
  "w-full rounded-2xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-secondary/60 px-3.5 py-2.5 text-sm text-tg-text outline-none transition focus:border-brand focus:bg-tg-bg focus:shadow-ring disabled:opacity-50";

function TierCard({
  draft,
  pool,
  onChange,
  onToggleModel,
  onDelete,
}: {
  draft: DraftTier;
  pool: ModelSpec[];
  onChange: (patch: Partial<DraftTier>) => void;
  onToggleModel: (id: string) => void;
  onDelete: () => void;
}) {
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const isFree = draft.key === "free";
  const Icon = isFree ? Layers : Crown;

  return (
    <Card>
      <div className="mb-3 flex items-center gap-2.5">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <Icon className="h-5 w-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <input
            type="text"
            value={draft.name}
            onChange={(e) => onChange({ name: e.target.value })}
            placeholder="Tier name"
            className="w-full bg-transparent text-sm font-semibold text-tg-text outline-none placeholder:text-tg-hint"
          />
          <p className="font-mono text-[11px] text-tg-hint">{draft.key}</p>
        </div>
        {!isFree &&
          (confirmingDelete ? (
            <div className="flex items-center gap-1.5">
              <Button size="sm" variant="secondary" onClick={() => setConfirmingDelete(false)}>
                Cancel
              </Button>
              <button
                type="button"
                onClick={onDelete}
                className="rounded-xl bg-red-500/12 px-3 py-1.5 text-xs font-semibold text-red-500 active:opacity-80"
              >
                Delete
              </button>
            </div>
          ) : (
            <button
              type="button"
              aria-label="Delete tier"
              onClick={() => setConfirmingDelete(true)}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-tg-hint transition active:bg-red-500/10 active:text-red-500"
            >
              <Trash2 className="h-4 w-4" aria-hidden />
            </button>
          ))}
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div>
          <label className="mb-1 block text-[11px] font-medium text-tg-hint">
            Daily limit
          </label>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            value={Number.isFinite(draft.daily_limit) ? draft.daily_limit : 0}
            onChange={(e) =>
              onChange({ daily_limit: Math.max(0, Number(e.target.value) || 0) })
            }
            className={numberFieldClass}
          />
        </div>
        <div>
          <label className="mb-1 flex items-center gap-1 text-[11px] font-medium text-tg-hint">
            <Coins className="h-3 w-3" aria-hidden />
            Stars
          </label>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            disabled={isFree}
            value={isFree ? 0 : Number.isFinite(draft.price_stars) ? draft.price_stars : 0}
            onChange={(e) =>
              onChange({ price_stars: Math.max(0, Number(e.target.value) || 0) })
            }
            className={numberFieldClass}
          />
        </div>
        <div>
          <label className="mb-1 block text-[11px] font-medium text-tg-hint">
            Period (days)
          </label>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            disabled={isFree}
            value={isFree ? 0 : Number.isFinite(draft.period_days) ? draft.period_days : 0}
            onChange={(e) =>
              onChange({ period_days: Math.max(0, Number(e.target.value) || 0) })
            }
            className={numberFieldClass}
          />
        </div>
      </div>

      <label className="mb-2 mt-3 flex items-center justify-between text-[11px] font-medium text-tg-hint">
        <span>Model package</span>
        <span>{draft.selected.size} selected</span>
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
                type="button"
                onClick={() => onToggleModel(m.id)}
                className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                  on
                    ? "border-brand/40 bg-brand/12 text-brand"
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
    </Card>
  );
}
