"use client";

import { useEffect, useState } from "react";
import { Save, Sparkles } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Card, SectionTitle } from "./Card";
import { CardSkeleton } from "./Skeleton";
import { Button, SaveMessage, type SaveStatus } from "./ui";

type Status = SaveStatus | "loading";

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
      setStatus("error");
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
    <Card>
      <SectionTitle icon={Sparkles}>System prompt</SectionTitle>
      {status === "loading" ? (
        <CardSkeleton lines={4} />
      ) : (
        <>
          <p className="mb-2 text-xs text-tg-hint">
            Defines the bot&apos;s persona. Sent with every message.{" "}
            {isDefault ? "Currently using the default." : "Custom prompt active."}
          </p>
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            rows={7}
            spellCheck={false}
            className="w-full resize-y rounded-xl border border-black/[0.1] dark:border-white/[0.12] bg-tg-bg/60 p-3 text-sm text-tg-text outline-none transition focus:border-tg-button"
            placeholder="You are a helpful assistant with long-term memory…"
          />
          <div className="mt-3 flex items-center justify-between gap-3">
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
        </>
      )}
    </Card>
  );
}
