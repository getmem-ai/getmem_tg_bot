"use client";

import { useRef, useState } from "react";
import { Download, LayoutTemplate, Upload } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { ConfigApplyResult } from "@/lib/types";
import { Card, SectionTitle } from "../Card";
import { Button } from "../ui";
import { TemplateGallery } from "./TemplateGallery";

function errMessage(err: unknown): string {
  return err instanceof ApiError && err.isForbidden
    ? "Admins only."
    : "Something went wrong.";
}

/** Apply starter templates + export/import the full bot config. */
export function TemplatesManager() {
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [result, setResult] = useState<ConfigApplyResult | null>(null);
  const [error, setError] = useState("");
  const [importing, setImporting] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function apply(key: string) {
    if (
      !window.confirm(
        "Apply this template? It overwrites the system prompt, welcome message, " +
          "branding, tiers and feature toggles. Provider keys and users are untouched.",
      )
    )
      return;
    setBusyKey(key);
    setResult(null);
    setError("");
    try {
      setResult(await api.applyTemplate(key));
    } catch (err: unknown) {
      setError(errMessage(err));
    } finally {
      setBusyKey(null);
    }
  }

  async function download() {
    setError("");
    try {
      const cfg = await api.exportConfig();
      const blob = new Blob([JSON.stringify(cfg, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "getmem-config.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(errMessage(err));
    }
  }

  async function onImportFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setImporting(true);
    setResult(null);
    setError("");
    try {
      const cfg = JSON.parse(await file.text()) as Record<string, unknown>;
      setResult(await api.importConfig(cfg));
    } catch (err: unknown) {
      setError(
        err instanceof SyntaxError ? "That file isn't valid JSON." : errMessage(err),
      );
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="space-y-3">
      <Card>
        <SectionTitle icon={LayoutTemplate}>Starter templates</SectionTitle>
        <p className="mb-3 text-xs text-muted">
          Apply a ready-made setup for a use case. Your provider keys and users
          stay as they are.
        </p>
        <TemplateGallery onApply={apply} busyKey={busyKey} />
      </Card>

      <Card>
        <SectionTitle icon={Download}>Backup & restore</SectionTitle>
        <p className="mb-3 text-xs text-muted">
          Download your full config (without API keys) to back it up or clone
          another bot, then import it elsewhere.
        </p>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" icon={Download} onClick={download}>
            Download config
          </Button>
          <Button
            size="sm"
            variant="secondary"
            icon={Upload}
            onClick={() => fileRef.current?.click()}
            disabled={importing}
          >
            {importing ? "Importing…" : "Import config"}
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept="application/json,.json"
            className="hidden"
            onChange={onImportFile}
          />
        </div>
      </Card>

      {result && (
        <Card>
          <p className="text-sm font-semibold text-text">
            {result.applied.length > 0
              ? `Applied: ${result.applied.join(", ")}.`
              : "Nothing to apply."}
          </p>
          {result.todo.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-xs text-muted">
              {result.todo.map((t) => (
                <li key={t}>{t}</li>
              ))}
            </ul>
          )}
        </Card>
      )}
      {error && <p className="px-1 text-xs text-red-500">{error}</p>}
    </div>
  );
}
