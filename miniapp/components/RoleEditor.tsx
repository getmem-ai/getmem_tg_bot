"use client";

import { useState } from "react";
import { Drama, Save } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Card } from "./Card";
import { Button, SaveMessage, Toggle, type SaveStatus } from "./ui";

const MAX_LEN = 1000;

interface RoleEditorProps {
  role: string | null;
  enabled: boolean;
  onSaved?: () => void;
}

/**
 * Lets a user give the assistant a persona for their chats. Disabled by
 * default — the user flips the toggle on to reveal the editor. Only rendered
 * when the admin has enabled personal roles globally.
 */
export function RoleEditor({ role, enabled, onSaved }: RoleEditorProps) {
  const [on, setOn] = useState(enabled);
  const [value, setValue] = useState(role ?? "");
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");
  const [toggling, setToggling] = useState(false);

  function errMessage(err: unknown): string {
    return err instanceof ApiError && err.isForbidden
      ? "Roles are disabled."
      : "Failed to save. Try again.";
  }

  function flashSaved() {
    setStatus("saved");
    setMessage("Saved");
    window.setTimeout(() => setStatus("idle"), 2000);
  }

  async function toggle(next: boolean) {
    if (toggling || status === "saving") return;
    setOn(next); // optimistic — reveal/hide the editor immediately
    setToggling(true);
    setStatus("saving");
    setMessage("");
    try {
      await api.setRole({ enabled: next });
      flashSaved();
      onSaved?.();
    } catch (err: unknown) {
      setOn(!next); // revert on failure
      setStatus("error");
      setMessage(errMessage(err));
    } finally {
      setToggling(false);
    }
  }

  async function save() {
    if (status === "saving") return;
    const trimmed = value.trim();
    setStatus("saving");
    setMessage("");
    try {
      const res = await api.setRole({ role: trimmed || null });
      setValue(res.role ?? "");
      flashSaved();
      onSaved?.();
    } catch (err: unknown) {
      setStatus("error");
      setMessage(errMessage(err));
    }
  }

  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="flex items-center gap-1.5 text-sm font-semibold text-tg-text">
            <Drama className="h-4 w-4 text-tg-button" aria-hidden />
            Personal role
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-tg-hint">
            Give the assistant a persona for your chats, e.g.{" "}
            <span className="text-tg-text">
              &quot;You are my English teacher&quot;
            </span>
            .
          </p>
        </div>
        <Toggle
          checked={on}
          onChange={(v) => void toggle(v)}
          disabled={toggling || status === "saving"}
          label="Enable personal role"
        />
      </div>

      {on && (
        <div className="mt-4 animate-fade-in">
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value.slice(0, MAX_LEN))}
            rows={4}
            maxLength={MAX_LEN}
            className="w-full resize-y rounded-xl border border-black/[0.1] dark:border-white/[0.12] bg-tg-bg/60 p-3 text-sm text-tg-text outline-none transition focus:border-tg-button"
            placeholder="e.g. You are my patient English teacher — correct my mistakes and explain briefly."
          />

          <div className="mt-3 flex items-center justify-between gap-3">
            <SaveMessage status={status} message={message} />
            <div className="flex items-center gap-3">
              <span className="text-xs tabular-nums text-tg-hint">
                {value.length}/{MAX_LEN}
              </span>
              <Button
                onClick={() => void save()}
                disabled={status === "saving"}
                icon={Save}
                size="sm"
              >
                {status === "saving" ? "Saving…" : "Save"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {!on && message && (
        <div className="mt-3">
          <SaveMessage status={status} message={message} />
        </div>
      )}
    </Card>
  );
}
