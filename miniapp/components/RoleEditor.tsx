"use client";

import { useState } from "react";
import { Drama, Save } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Card, SectionTitle } from "./Card";
import { Button, SaveMessage, type SaveStatus } from "./ui";

const MAX_LEN = 1000;

interface RoleEditorProps {
  role: string | null;
  onSaved?: () => void;
}

/**
 * Lets a user describe the role the assistant should play in their chats.
 * Only rendered when the admin has enabled personal roles. Saving sends the
 * trimmed text (or null when cleared) to PUT /me/role.
 */
export function RoleEditor({ role, onSaved }: RoleEditorProps) {
  const [value, setValue] = useState(role ?? "");
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  async function persist(next: string | null) {
    setStatus("saving");
    setMessage("");
    try {
      const res = await api.setRole(next);
      setValue(res.role ?? "");
      setStatus("saved");
      setMessage("Saved");
      window.setTimeout(() => setStatus("idle"), 2000);
      onSaved?.();
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.isForbidden
          ? "Roles are disabled."
          : "Failed to save. Try again.",
      );
    }
  }

  function save() {
    const trimmed = value.trim();
    void persist(trimmed || null);
  }

  function clear() {
    setValue("");
    void persist(null);
  }

  const hasRole = value.trim().length > 0;

  return (
    <Card>
      <SectionTitle
        icon={Drama}
        right={
          hasRole ? (
            <button
              type="button"
              onClick={clear}
              disabled={status === "saving"}
              className="text-xs font-medium text-tg-hint transition hover:text-tg-text disabled:opacity-50"
            >
              Clear
            </button>
          ) : undefined
        }
      >
        Personal role
      </SectionTitle>

      <p className="mb-2 text-xs text-tg-hint">
        This is added to the assistant&apos;s instructions for your chats.
      </p>

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
