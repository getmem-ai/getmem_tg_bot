"use client";

import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { TemplatesResponse } from "@/lib/types";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import { Button } from "../ui";

interface TemplateGalleryProps {
  onApply: (key: string) => void;
  busyKey: string | null;
}

/** A grid of starter-bot presets. Selecting one calls `onApply(key)`. */
export function TemplateGallery({ onApply, busyKey }: TemplateGalleryProps) {
  const { data, error, loading, reload } = useApi<TemplatesResponse>(() =>
    api.getTemplates(),
  );

  if (loading) return <CardSkeleton lines={4} />;
  if (error) return <ErrorState error={error} onRetry={reload} />;
  if (!data) return null;

  return (
    <div className="grid grid-cols-1 gap-2">
      {data.templates.map((t) => (
        <div
          key={t.key}
          className="flex items-center gap-3 rounded-2xl border border-border bg-surface-2/50 p-3"
        >
          <span className="text-2xl" aria-hidden>
            {t.emoji}
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-text">{t.name}</p>
            <p className="text-xs text-muted">{t.description}</p>
          </div>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => onApply(t.key)}
            disabled={busyKey !== null}
          >
            {busyKey === t.key ? "Applying…" : "Apply"}
          </Button>
        </div>
      ))}
    </div>
  );
}
