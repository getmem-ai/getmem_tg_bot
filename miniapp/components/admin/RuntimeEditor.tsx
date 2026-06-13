"use client";

import { useState } from "react";
import { Drama, Mic, PauseCircle, Save, SlidersHorizontal } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { RuntimeResponse } from "@/lib/types";
import { Card, SectionTitle } from "../Card";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import { Button, SaveMessage, Toggle, type SaveStatus } from "../ui";

/** Voice transcription toggle + per-model rotation kill-switches. */
export function RuntimeEditor() {
  const { data, error, loading, reload } = useApi<RuntimeResponse>(() =>
    api.getRuntime(),
  );

  if (loading) return <CardSkeleton lines={4} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  return <RuntimeForm initial={data} />;
}

function RuntimeForm({ initial }: { initial: RuntimeResponse }) {
  const [voice, setVoice] = useState(initial.voice_enabled);
  const [rolesEnabled, setRolesEnabled] = useState(initial.user_roles_enabled);
  const [paused, setPaused] = useState(initial.generation_paused);
  const [maxTokens, setMaxTokens] = useState<string>(String(initial.max_tokens));
  const [disabled, setDisabled] = useState<Set<string>>(
    new Set(initial.disabled_models),
  );
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  function toggleModel(id: string) {
    setDisabled((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function save() {
    setStatus("saving");
    setMessage("");
    // Clamp to a non-negative integer; blank/invalid falls back to 0 (default).
    const parsed = Math.max(0, Math.floor(Number(maxTokens)));
    const tokens = Number.isFinite(parsed) ? parsed : 0;
    try {
      const res = await api.setRuntime({
        voice_enabled: voice,
        disabled_models: Array.from(disabled),
        user_roles_enabled: rolesEnabled,
        generation_paused: paused,
        max_tokens: tokens,
      });
      setVoice(res.voice_enabled);
      setRolesEnabled(res.user_roles_enabled);
      setPaused(res.generation_paused);
      setMaxTokens(String(res.max_tokens));
      setDisabled(new Set(res.disabled_models));
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
      <SectionTitle icon={SlidersHorizontal}>Runtime</SectionTitle>

      <div
        className={`flex items-center gap-3 rounded-xl border px-3 py-2.5 ${
          paused
            ? "border-red-500/30 bg-red-500/5"
            : "border-black/[0.06] dark:border-white/[0.08] bg-tg-bg/40"
        }`}
      >
        <span
          className={`flex h-8 w-8 items-center justify-center rounded-lg ${
            paused ? "bg-red-500/15 text-red-500" : "bg-tg-button/10 text-tg-button"
          }`}
        >
          <PauseCircle className="h-4 w-4" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Pause bot</p>
          <p className="text-xs text-tg-hint">
            Kill-switch — stops generating replies for everyone.
          </p>
        </div>
        <Toggle checked={paused} onChange={setPaused} label="Pause bot" />
      </div>
      {paused && (
        <p className="mt-1.5 text-xs font-medium text-red-500">
          Bot is paused — users get a maintenance message
        </p>
      )}

      <div className="mt-2 flex items-center gap-3 rounded-xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-bg/40 px-3 py-2.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-tg-button/10 text-tg-button">
          <Mic className="h-4 w-4" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Voice transcription</p>
          <p className="text-xs text-tg-hint">
            Transcribe incoming voice messages.
          </p>
        </div>
        <Toggle checked={voice} onChange={setVoice} label="Voice transcription" />
      </div>

      <div className="mt-2 flex items-center gap-3 rounded-xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-bg/40 px-3 py-2.5">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-tg-button/10 text-tg-button">
          <Drama className="h-4 w-4" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Allow users to set a personal role</p>
          <p className="text-xs text-tg-hint">
            Let users define their own assistant role in Settings.
          </p>
        </div>
        <Toggle
          checked={rolesEnabled}
          onChange={setRolesEnabled}
          label="Allow personal roles"
        />
      </div>

      <div className="mt-2 rounded-xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-bg/40 px-3 py-2.5">
        <div className="flex items-center gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">Max tokens per reply</p>
            <p className="text-xs text-tg-hint">
              Caps response length to control cost. 0 = provider default.
            </p>
          </div>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            step={1}
            value={maxTokens}
            onChange={(e) => setMaxTokens(e.target.value)}
            aria-label="Max tokens per reply"
            placeholder="0"
            className="w-24 rounded-lg border border-black/[0.08] dark:border-white/[0.12] bg-tg-bg px-2.5 py-1.5 text-right text-sm text-tg-text outline-none focus:border-tg-button"
          />
        </div>
      </div>

      <p className="mb-2 mt-4 text-xs font-medium text-tg-hint">
        Models in rotation
      </p>
      {initial.all_models.length === 0 ? (
        <p className="text-xs text-tg-hint">No models configured.</p>
      ) : (
        <ul className="space-y-1">
          {initial.all_models.map((m) => {
            const off = disabled.has(m.id);
            return (
              <li
                key={m.id}
                className="flex items-center gap-3 rounded-xl px-1 py-1.5"
              >
                <div className="min-w-0 flex-1">
                  <p
                    className={`truncate text-sm ${off ? "text-tg-hint line-through" : "text-tg-text"}`}
                  >
                    {m.label}
                  </p>
                  <p className="truncate text-xs text-tg-hint">{m.id}</p>
                </div>
                <Toggle
                  checked={!off}
                  onChange={() => toggleModel(m.id)}
                  label={`Toggle ${m.label}`}
                />
              </li>
            );
          })}
        </ul>
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
