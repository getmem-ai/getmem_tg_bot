"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Card, SectionTitle } from "./Card";
import { CardSkeleton } from "./Skeleton";

type Status = "idle" | "loading" | "saving" | "saved" | "error";

/**
 * Admin-only editor for the bot's system prompt (persona). The prompt is stored
 * in the database, so saving here changes the bot's behaviour for everyone
 * immediately — no redeploy. Only rendered when the user is_admin.
 */
export function PromptEditor() {
  const [value, setValue] = useState("");
  const [isDefault, setIsDefault] = useState(true);
  const [status, setStatus] = useState<Status>("loading");
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    let active = true;
    api
      .getPrompt()
      .then((res) => {
        if (!active) return;
        setValue(res.system_prompt);
        setIsDefault(res.is_default);
        setStatus("idle");
      })
      .catch((err: unknown) => {
        if (!active) return;
        // A non-admin gets 403 — just hide the editor by staying in error.
        setStatus("error");
        setMessage(
          err instanceof ApiError && err.isForbidden
            ? ""
            : "Couldn't load the prompt.",
        );
      });
    return () => {
      active = false;
    };
  }, []);

  async function save() {
    const trimmed = value.trim();
    if (!trimmed) {
      setMessage("Prompt can't be empty.");
      return;
    }
    setStatus("saving");
    setMessage("");
    try {
      const res = await api.setPrompt(trimmed);
      setValue(res.system_prompt);
      setIsDefault(res.is_default);
      setStatus("saved");
      setMessage("Saved — applies to all users now.");
      window.setTimeout(() => setStatus("idle"), 2500);
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.isForbidden
          ? "Admins only."
          : "Failed to save. Try again.",
      );
    }
  }

  // Hidden for non-admins (403 on load).
  if (status === "error" && message === "") return null;

  return (
    <div className="space-y-3">
      <SectionTitle>Bot system prompt</SectionTitle>
      <Card>
        {status === "loading" ? (
          <CardSkeleton lines={4} />
        ) : (
          <>
            <p className="mb-2 text-xs text-tg-hint">
              Defines what the bot is (its persona/domain). Sent with every
              message.{" "}
              {isDefault ? (
                <span className="text-tg-hint">Currently using the default.</span>
              ) : (
                <span className="text-tg-hint">Custom prompt active.</span>
              )}
            </p>
            <textarea
              value={value}
              onChange={(e) => setValue(e.target.value)}
              rows={7}
              spellCheck={false}
              className="w-full resize-y rounded-xl border border-black/[0.1] dark:border-white/[0.12] bg-tg-bg/60 p-3 text-sm text-tg-text outline-none focus:border-tg-button"
              placeholder="You are a helpful assistant with long-term memory…"
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              <span
                className={
                  status === "saved"
                    ? "text-xs text-green-500"
                    : "text-xs text-tg-hint"
                }
              >
                {message}
              </span>
              <button
                onClick={save}
                disabled={status === "saving"}
                className="shrink-0 rounded-xl bg-tg-button px-4 py-2 text-sm font-semibold text-tg-button-text disabled:opacity-60"
              >
                {status === "saving" ? "Saving…" : "Save prompt"}
              </button>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
