"use client";

import { useState } from "react";
import { Check, KeyRound, Loader2, Lock, Save, Server, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { ProviderConfig, ProvidersResponse } from "@/lib/types";
import { Card } from "../Card";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import { Button, SaveMessage, Toggle, type SaveStatus } from "../ui";

function parseModels(text: string): string[] {
  return text
    .split(/[\n,]/)
    .map((s) => s.trim())
    .filter(Boolean);
}

/** Per-provider config: enable, edit model list, set write-only API key. */
export function ProvidersEditor() {
  const { data, error, loading, reload } = useApi<ProvidersResponse>(() =>
    api.getProviders(),
  );

  if (loading) return <CardSkeleton lines={5} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="space-y-3">
      {data.providers.map((p) => (
        <ProviderRow key={p.name} provider={p} />
      ))}
    </div>
  );
}

function ProviderRow({ provider }: { provider: ProviderConfig }) {
  const [enabled, setEnabled] = useState(provider.enabled);
  const [modelsText, setModelsText] = useState(provider.models.join("\n"));
  const [apiKey, setApiKey] = useState("");
  const [hasKey, setHasKey] = useState(provider.has_key);
  const [keyMasked, setKeyMasked] = useState(provider.key_masked);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    ok: boolean;
    detail: string;
  } | null>(null);

  const readOnlyKey = provider.is_default;

  async function test() {
    setTesting(true);
    setTestResult(null);
    const models = parseModels(modelsText);
    try {
      const res = await api.testProvider(provider.name, {
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
        ...(models[0] ? { model: models[0] } : {}),
      });
      setTestResult(res);
    } catch (err: unknown) {
      setTestResult({
        ok: false,
        detail:
          err instanceof ApiError && err.isForbidden
            ? "Admins only."
            : "Test failed.",
      });
    } finally {
      setTesting(false);
    }
  }

  async function save() {
    setStatus("saving");
    setMessage("");
    try {
      const res = await api.setProvider({
        name: provider.name,
        enabled,
        models: parseModels(modelsText),
        // Only send the key when the admin actually typed a new one.
        ...(apiKey.trim() ? { api_key: apiKey.trim() } : {}),
      });
      setEnabled(res.enabled);
      setModelsText(res.models.join("\n"));
      setHasKey(res.has_key);
      setKeyMasked(res.key_masked);
      setApiKey("");
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
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <Server className="h-5 w-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold capitalize">
              {provider.name}
            </p>
            {provider.is_default && (
              <span className="rounded-full bg-brand/12 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand">
                Default
              </span>
            )}
          </div>
          {provider.note && (
            <p className="truncate text-xs text-tg-hint">{provider.note}</p>
          )}
        </div>
        <Toggle
          checked={enabled}
          onChange={setEnabled}
          disabled={provider.is_default}
          label={`Enable ${provider.name}`}
        />
      </div>

      {/* API key */}
      <label className="mb-1 flex items-center gap-1.5 text-xs font-medium text-tg-hint">
        {readOnlyKey ? (
          <Lock className="h-3.5 w-3.5" aria-hidden />
        ) : (
          <KeyRound className="h-3.5 w-3.5" aria-hidden />
        )}
        API key
      </label>
      {readOnlyKey ? (
        <p className="rounded-xl border border-black/[0.08] dark:border-white/[0.12] bg-tg-bg/40 px-3 py-2 text-xs text-tg-hint">
          {hasKey ? keyMasked ?? "Configured" : "Managed by environment"}
        </p>
      ) : (
        <>
          {hasKey && (
            <p className="mb-1 text-xs text-tg-hint">
              Current: <span className="font-mono">{keyMasked}</span>
            </p>
          )}
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            autoComplete="off"
            spellCheck={false}
            placeholder={hasKey ? "Replace key (leave blank to keep)" : "Paste API key"}
            className="w-full rounded-2xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-secondary/60 px-3.5 py-2.5 text-sm text-tg-text outline-none transition focus:border-brand focus:bg-tg-bg focus:shadow-ring"
          />
        </>
      )}

      {/* Models */}
      <label className="mb-1 mt-3 block text-xs font-medium text-tg-hint">
        Models (one per line or comma-separated)
      </label>
      <textarea
        value={modelsText}
        onChange={(e) => setModelsText(e.target.value)}
        rows={3}
        spellCheck={false}
        className="w-full resize-y rounded-2xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-secondary/60 p-3.5 font-mono text-xs text-tg-text outline-none transition focus:border-brand focus:bg-tg-bg focus:shadow-ring"
        placeholder="gpt-4o&#10;gpt-4o-mini"
      />

      {testResult && (
        <p
          className={`mt-3 flex items-start gap-1.5 text-xs ${
            testResult.ok ? "text-success" : "text-danger"
          }`}
        >
          {testResult.ok ? (
            <Check className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          ) : (
            <X className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          )}
          <span className="min-w-0 break-words">{testResult.detail}</span>
        </p>
      )}

      <div className="mt-3 flex items-center justify-between gap-3">
        <SaveMessage status={status} message={message} />
        <div className="flex items-center gap-2">
          <Button
            onClick={test}
            disabled={testing}
            variant="secondary"
            size="sm"
          >
            {testing ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : null}
            {testing ? "Testing…" : "Test"}
          </Button>
          <Button
            onClick={save}
            disabled={status === "saving"}
            icon={Save}
            size="sm"
          >
            {status === "saving" ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>
    </Card>
  );
}
