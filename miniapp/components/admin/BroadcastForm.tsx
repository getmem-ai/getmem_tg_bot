"use client";

import { useState } from "react";
import { Megaphone, Send } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { TiersResponse } from "@/lib/types";
import { Card, SectionTitle } from "../Card";
import { Button, Field, SaveMessage, Select, type SaveStatus } from "../ui";

const MAX_LEN = 4096;

/** Compose and queue a plain-text broadcast to all users or a single tier. */
export function BroadcastForm() {
  // Tiers power the optional audience selector; failure here is non-fatal —
  // we just fall back to "All users".
  const { data: tiersData } = useApi<TiersResponse>(() => api.getTiers());
  const tiers = tiersData?.tiers ?? [];

  const [text, setText] = useState("");
  const [tier, setTier] = useState<string>(""); // "" → all users
  const [confirming, setConfirming] = useState(false);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  const trimmed = text.trim();
  const sending = status === "saving";
  const canSend = trimmed.length > 0 && !sending;

  function reset() {
    setConfirming(false);
  }

  async function send() {
    setStatus("saving");
    setMessage("");
    setConfirming(false);
    try {
      const res = await api.broadcast(trimmed, tier || null);
      setText("");
      setStatus("saved");
      setMessage(`Queued for ${res.queued} users`);
      window.setTimeout(() => setStatus("idle"), 4000);
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.isForbidden
          ? "Admins only."
          : "Failed to send.",
      );
    }
  }

  return (
    <Card>
      <SectionTitle
        icon={Megaphone}
        right={
          <span className="text-xs text-tg-hint">
            {text.length}/{MAX_LEN}
          </span>
        }
      >
        Broadcast
      </SectionTitle>

      <textarea
        value={text}
        maxLength={MAX_LEN}
        onChange={(e) => {
          setText(e.target.value);
          reset();
        }}
        placeholder="Write a message to send to your users…"
        rows={5}
        className="w-full resize-y rounded-2xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-secondary/60 px-3.5 py-3 text-sm text-tg-text outline-none transition focus:border-brand focus:bg-tg-bg focus:shadow-ring"
      />

      <div className="mt-3">
        <Field label="Audience">
          <Select
            value={tier}
            onChange={(v) => {
              setTier(v);
              reset();
            }}
            options={[
              { value: "", label: "All users" },
              ...tiers.map((t) => ({ value: t.key, label: t.name })),
            ]}
          />
        </Field>
      </div>

      <p className="mt-3 text-xs text-tg-hint">
        Plain text only. Sent gradually to respect Telegram limits.
      </p>

      <div className="mt-4 flex items-center justify-between gap-3">
        <SaveMessage status={status} message={message} />
        {confirming ? (
          <div className="flex items-center gap-2">
            <Button onClick={reset} variant="secondary" size="sm">
              Cancel
            </Button>
            <Button onClick={send} disabled={!canSend} icon={Send} size="sm">
              Confirm
            </Button>
          </div>
        ) : (
          <Button
            onClick={() => setConfirming(true)}
            disabled={!canSend}
            icon={Send}
            size="sm"
          >
            {sending ? "Sending…" : "Send"}
          </Button>
        )}
      </div>
    </Card>
  );
}
