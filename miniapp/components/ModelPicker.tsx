"use client";

import { useState, type ReactNode } from "react";
import { Check, Cpu, Shuffle } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { ModelSpec } from "@/lib/types";
import { Card, SectionTitle } from "./Card";
import { SaveMessage, type SaveStatus } from "./ui";

interface ModelPickerProps {
  available: ModelSpec[];
  current: string | null;
  /** Called with the persisted value after a successful save. */
  onChange?: (model: string | null) => void;
}

const PROVIDER_LABEL: Record<string, string> = {
  openrouter: "OpenRouter",
  openai: "OpenAI",
  anthropic: "Anthropic",
};

/** Lets the user choose Auto rotation or a specific model from their tier. */
export function ModelPicker({ available, current, onChange }: ModelPickerProps) {
  const [selected, setSelected] = useState<string | null>(current);
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState<string | null>(null);

  async function choose(model: string | null) {
    if (model === selected || status === "saving") return;
    setStatus("saving");
    setMessage("");
    setPending(model);
    try {
      const res = await api.setModel(model);
      setSelected(res.preferred_model);
      onChange?.(res.preferred_model);
      setStatus("saved");
      setMessage("Saved");
      window.setTimeout(() => setStatus("idle"), 2000);
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.isForbidden
          ? "Not allowed for your plan."
          : "Couldn't save. Try again.",
      );
    } finally {
      setPending(null);
    }
  }

  return (
    <Card>
      <SectionTitle
        icon={Cpu}
        right={<SaveMessage status={status} message={message} />}
      >
        Model
      </SectionTitle>

      <ul className="-mx-1 space-y-1">
        <ModelRow
          icon={<Shuffle className="h-4 w-4" aria-hidden />}
          title="Auto"
          subtitle="Rotate across available models"
          active={selected === null}
          busy={status === "saving" && pending === null}
          onClick={() => choose(null)}
        />
        {available.map((m) => (
          <ModelRow
            key={m.id}
            title={m.label}
            subtitle={PROVIDER_LABEL[m.provider] ?? m.provider}
            active={selected === m.id}
            busy={status === "saving" && pending === m.id}
            onClick={() => choose(m.id)}
          />
        ))}
      </ul>

      {available.length === 0 && (
        <p className="px-1 pt-2 text-xs text-tg-hint">
          No specific models available on your plan — Auto picks the best one.
        </p>
      )}
    </Card>
  );
}

function ModelRow({
  title,
  subtitle,
  active,
  busy,
  onClick,
  icon,
}: {
  title: string;
  subtitle: string;
  active: boolean;
  busy: boolean;
  onClick: () => void;
  icon?: ReactNode;
}) {
  return (
    <li>
      <button
        onClick={onClick}
        disabled={busy}
        className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
          active
            ? "bg-tg-button/10 ring-1 ring-inset ring-tg-button/30"
            : "active:bg-black/[0.04] dark:active:bg-white/[0.06]"
        }`}
      >
        {icon && (
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-tg-hint/12 text-tg-hint">
            {icon}
          </span>
        )}
        <span className="min-w-0 flex-1">
          <span className="block truncate text-sm font-medium text-tg-text">
            {title}
          </span>
          <span className="block truncate text-xs text-tg-hint">{subtitle}</span>
        </span>
        <span
          className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full transition ${
            active ? "bg-tg-button text-tg-button-text" : "text-transparent"
          }`}
        >
          <Check className="h-3.5 w-3.5" aria-hidden />
        </span>
      </button>
    </li>
  );
}
