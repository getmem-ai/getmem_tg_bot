"use client";

import { useState } from "react";
import {
  Drama,
  Image as ImageIcon,
  MessageSquareText,
  Mic,
  PauseCircle,
  Save,
  SlidersHorizontal,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { RuntimeResponse } from "@/lib/types";
import { Card, SectionTitle } from "../Card";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import { Button, Input, SaveMessage, Toggle, type SaveStatus } from "../ui";

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
  const [vision, setVision] = useState(initial.vision_enabled);
  const [visionModel, setVisionModel] = useState(initial.vision_model);
  const [welcome, setWelcome] = useState(initial.welcome_message);
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
        vision_enabled: vision,
        vision_model: visionModel.trim() || undefined,
        welcome_message: welcome,
      });
      setVoice(res.voice_enabled);
      setRolesEnabled(res.user_roles_enabled);
      setPaused(res.generation_paused);
      setMaxTokens(String(res.max_tokens));
      setVision(res.vision_enabled);
      setVisionModel(res.vision_model);
      setWelcome(res.welcome_message);
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
        className={`flex items-center gap-3 rounded-2xl border px-3.5 py-3 ${
          paused
            ? "border-red-500/30 bg-red-500/5"
            : "border-black/[0.04] dark:border-white/[0.06] bg-tg-secondary/50"
        }`}
      >
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-2xl ${
            paused ? "bg-red-500/15 text-red-500" : "bg-brand/10 text-brand"
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

      <div className="mt-2 flex items-center gap-3 rounded-2xl border border-black/[0.04] dark:border-white/[0.06] bg-tg-secondary/50 px-3.5 py-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <Mic className="h-5 w-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Voice transcription</p>
          <p className="text-xs text-tg-hint">
            Transcribe incoming voice messages.
          </p>
        </div>
        <Toggle checked={voice} onChange={setVoice} label="Voice transcription" />
      </div>

      <div className="mt-2 flex items-center gap-3 rounded-2xl border border-black/[0.04] dark:border-white/[0.06] bg-tg-secondary/50 px-3.5 py-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <Drama className="h-5 w-5" aria-hidden />
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

      {/* Vision (image understanding) */}
      <div className="mt-2 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <ImageIcon className="h-5 w-5" aria-hidden />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">Image understanding (vision)</p>
            <p className="text-xs text-muted">
              Let users send photos (e.g. count calories from a meal).
            </p>
          </div>
          <Toggle checked={vision} onChange={setVision} label="Vision" />
        </div>
        {vision && (
          <div className="mt-3">
            <Input
              value={visionModel}
              onChange={(e) => setVisionModel(e.target.value)}
              placeholder="google/gemma-4-31b-it:free"
              aria-label="Vision model"
            />
            <p className="mt-1 text-xs text-muted">
              Must be a vision-capable model (OpenRouter id). Default works out of
              the box.
            </p>
          </div>
        )}
      </div>

      {/* Welcome message */}
      <div className="mt-2 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
            <MessageSquareText className="h-5 w-5" aria-hidden />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium">Welcome message (/start)</p>
            <p className="text-xs text-muted">
              Use <code>{"{name}"}</code> for the user&rsquo;s name. Empty = default.
            </p>
          </div>
        </div>
        <textarea
          value={welcome}
          onChange={(e) => setWelcome(e.target.value)}
          rows={4}
          placeholder="👋 Hi {name}! I'm your assistant…"
          className="mt-3 w-full resize-y rounded-2xl border border-border bg-surface-2/60 p-3 text-sm text-text outline-none transition focus:border-primary focus:bg-surface focus:shadow-ring"
        />
      </div>

      <div className="mt-2 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
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
            className="w-24 rounded-xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-bg px-2.5 py-2 text-right text-sm text-tg-text outline-none transition focus:border-brand focus:shadow-ring"
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
