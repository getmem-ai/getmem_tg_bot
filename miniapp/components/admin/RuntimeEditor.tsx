"use client";

import { useState } from "react";
import { Mic, Save, SlidersHorizontal } from "lucide-react";
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
    try {
      const res = await api.setRuntime({
        voice_enabled: voice,
        disabled_models: Array.from(disabled),
      });
      setVoice(res.voice_enabled);
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

      <div className="flex items-center gap-3 rounded-xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-bg/40 px-3 py-2.5">
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
