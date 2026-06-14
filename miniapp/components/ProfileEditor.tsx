"use client";

import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Camera, Trash2, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { User } from "@/lib/types";
import { fileToAvatarDataUrl } from "@/lib/image";
import { haptic } from "@/lib/telegram";
import {
  Button,
  Field,
  SaveMessage,
  SegmentedControl,
  Select,
  type SaveStatus,
  type SelectOption,
} from "./ui";
import { TimezonePicker } from "./ui/TimezonePicker";

interface ProfileEditorProps {
  user: User;
  onClose: () => void;
  onSaved: () => void;
}

const LANGUAGES: SelectOption<string>[] = [
  { value: "auto", label: "Auto (match the user)" },
  { value: "en", label: "English" },
  { value: "ru", label: "Russian" },
  { value: "es", label: "Spanish" },
  { value: "de", label: "German" },
  { value: "fr", label: "French" },
  { value: "pt", label: "Portuguese" },
  { value: "it", label: "Italian" },
  { value: "uk", label: "Ukrainian" },
  { value: "pl", label: "Polish" },
  { value: "tr", label: "Turkish" },
  { value: "zh", label: "Chinese" },
  { value: "ja", label: "Japanese" },
  { value: "ko", label: "Korean" },
  { value: "ar", label: "Arabic" },
  { value: "hi", label: "Hindi" },
  { value: "id", label: "Indonesian" },
];

const STYLES: { value: string; label: string }[] = [
  { value: "default", label: "Default" },
  { value: "friendly", label: "Friendly" },
  { value: "formal", label: "Formal" },
];

const LENGTHS: { value: string; label: string }[] = [
  { value: "default", label: "Default" },
  { value: "concise", label: "Concise" },
  { value: "detailed", label: "Detailed" },
];

export function ProfileEditor({ user, onClose, onSaved }: ProfileEditorProps) {
  const [avatar, setAvatar] = useState<string | null>(user.avatar);
  const [language, setLanguage] = useState(user.reply_language ?? "auto");
  const [style, setStyle] = useState(user.reply_style ?? "default");
  const [length, setLength] = useState(user.reply_length ?? "default");
  const [timezone, setTimezone] = useState(user.timezone || "UTC");
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [mounted, setMounted] = useState(false);

  // Portal to <body> so the sheet escapes the profile card's stacking context
  // and overflow; lock background scroll while open.
  useEffect(() => {
    setMounted(true);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, []);

  const initial =
    user.first_name?.trim()?.[0] || user.username?.trim()?.[0] || "U";

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking the same file
    if (!file) return;
    try {
      setMessage("");
      const dataUrl = await fileToAvatarDataUrl(file);
      setAvatar(dataUrl);
      haptic("light");
    } catch {
      setStatus("error");
      setMessage("Couldn't read that image.");
    }
  }

  async function save() {
    setStatus("saving");
    setMessage("");
    try {
      await api.setProfile({
        avatar,
        reply_language: language,
        reply_style: style,
        reply_length: length,
        timezone,
      });
      haptic("medium");
      onSaved();
      onClose();
    } catch (err: unknown) {
      setStatus("error");
      setMessage(
        err instanceof ApiError && err.status === 413
          ? "Image is too large — try a smaller one."
          : "Failed to save.",
      );
    }
  }

  if (!mounted) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-end justify-center sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-label="Edit profile"
    >
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div className="animate-fade-in relative max-h-[90vh] w-full max-w-md overflow-y-auto rounded-t-card-lg border border-border bg-surface p-5 shadow-pop sm:rounded-card-lg">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-text">Edit profile</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition active:bg-surface-2"
          >
            <X className="h-5 w-5" aria-hidden />
          </button>
        </div>

        {/* Avatar */}
        <div className="flex items-center gap-4">
          <div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-grad-primary text-2xl font-bold uppercase text-white shadow-soft ring-1 ring-border">
            {avatar ? (
              // Avatar is a local/stored data URL; next/image isn't needed.
              // eslint-disable-next-line @next/next/no-img-element
              <img src={avatar} alt="" className="h-full w-full object-cover" />
            ) : (
              initial
            )}
          </div>
          <div className="flex flex-col gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={Camera}
              onClick={() => fileRef.current?.click()}
            >
              {avatar ? "Change photo" : "Upload photo"}
            </Button>
            {avatar && (
              <Button
                variant="ghost"
                size="sm"
                icon={Trash2}
                onClick={() => setAvatar(null)}
              >
                Remove
              </Button>
            )}
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={onPick}
          />
        </div>

        <div className="mt-5 space-y-4">
          <Field label="Reply language">
            <Select options={LANGUAGES} value={language} onChange={setLanguage} />
          </Field>

          <Field label="Reply tone">
            <SegmentedControl options={STYLES} value={style} onChange={setStyle} />
          </Field>

          <Field label="Reply length">
            <SegmentedControl options={LENGTHS} value={length} onChange={setLength} />
          </Field>

          <Field
            label="Timezone"
            hint="Used to schedule reminders in your local time."
          >
            <TimezonePicker value={timezone} onChange={setTimezone} />
          </Field>
        </div>

        <div className="mt-6 flex items-center justify-between gap-3">
          <SaveMessage status={status} message={message} />
          <Button onClick={save} disabled={status === "saving"} size="sm">
            {status === "saving" ? "Saving…" : "Save"}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
