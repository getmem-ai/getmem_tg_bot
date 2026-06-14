"use client";

import { useState, type ComponentType } from "react";
import {
  AlarmClock,
  BadgeCheck,
  Drama,
  Image as ImageIcon,
  Layers,
  MessageSquareText,
  Mic,
  PauseCircle,
  Power,
  Save,
  SlidersHorizontal,
  Sparkles,
  Zap,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import type { RuntimeResponse } from "@/lib/types";
import { Card, SectionTitle } from "../Card";
import { CardSkeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import {
  Button,
  Field,
  Input,
  SaveMessage,
  Select,
  Toggle,
  type SaveStatus,
  type SelectOption,
} from "../ui";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

const PROVIDER_LABELS: Record<string, string> = {
  openrouter: "OpenRouter",
  openai: "OpenAI",
  anthropic: "Anthropic",
};

function providerLabel(p: string): string {
  return PROVIDER_LABELS[p] ?? p.charAt(0).toUpperCase() + p.slice(1);
}

/** A consistent labelled toggle row used across every settings group. */
function ToggleRow({
  icon: Icon,
  title,
  desc,
  checked,
  onChange,
  label,
  tone = "default",
}: {
  icon?: IconType;
  title: string;
  desc?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
  tone?: "default" | "danger";
}) {
  const danger = tone === "danger" && checked;
  return (
    <div
      className={`flex items-center gap-3 rounded-2xl border px-3.5 py-3 ${
        danger ? "border-red-500/30 bg-red-500/5" : "border-border bg-surface-2/50"
      }`}
    >
      {Icon && (
        <span
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl ${
            danger ? "bg-red-500/15 text-red-500" : "bg-primary/10 text-primary"
          }`}
        >
          <Icon className="h-5 w-5" aria-hidden />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-text">{title}</p>
        {desc && <p className="text-xs text-muted">{desc}</p>}
      </div>
      <Toggle checked={checked} onChange={onChange} label={label} />
    </div>
  );
}

/** Bot behaviour, features, limits, content & model rotation — grouped. */
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
  const [rolesEnabled, setRolesEnabled] = useState(initial.user_roles_enabled);
  const [paused, setPaused] = useState(initial.generation_paused);
  const [maxTokens, setMaxTokens] = useState<string>(String(initial.max_tokens));
  const [vision, setVision] = useState(initial.vision_enabled);
  // Vision model is selected as "provider:id" (ids may contain ':', so we only
  // split on the first colon when saving).
  const [visionSel, setVisionSel] = useState(
    `${initial.vision_provider}:${initial.vision_model}`,
  );
  const [visionPremiumOnly, setVisionPremiumOnly] = useState(
    initial.vision_premium_only,
  );
  const [streaming, setStreaming] = useState(initial.streaming_enabled);
  const [scheduling, setScheduling] = useState(initial.scheduling_enabled);
  const [welcome, setWelcome] = useState(initial.welcome_message);
  const [brandName, setBrandName] = useState(initial.brand_name);
  const [brandTagline, setBrandTagline] = useState(initial.brand_tagline);
  const [disabled, setDisabled] = useState<Set<string>>(
    new Set(initial.disabled_models),
  );
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");

  // Options for the vision-model dropdown: every configured model, keyed by
  // "provider:id", with the current selection guaranteed to be present.
  const visionOptions: SelectOption<string>[] = [];
  const seenVision = new Set<string>();
  const addVisionOption = (provider: string, id: string, label?: string) => {
    const v = `${provider}:${id}`;
    if (seenVision.has(v)) return;
    seenVision.add(v);
    visionOptions.push({
      value: v,
      label: label || id,
      hint: providerLabel(provider),
    });
  };
  addVisionOption(initial.vision_provider, initial.vision_model);
  for (const m of initial.all_models) addVisionOption(m.provider, m.id, m.label);

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
    // Clamp to a non-negative integer; blank/invalid falls back to 0 (default).
    const parsed = Math.max(0, Math.floor(Number(maxTokens)));
    const tokens = Number.isFinite(parsed) ? parsed : 0;
    const colon = visionSel.indexOf(":");
    const visionProvider = colon >= 0 ? visionSel.slice(0, colon) : "openrouter";
    const visionModelId = colon >= 0 ? visionSel.slice(colon + 1) : visionSel;
    try {
      const res = await api.setRuntime({
        voice_enabled: voice,
        disabled_models: Array.from(disabled),
        user_roles_enabled: rolesEnabled,
        generation_paused: paused,
        max_tokens: tokens,
        vision_enabled: vision,
        vision_model: visionModelId.trim() || undefined,
        vision_provider: visionProvider,
        vision_premium_only: visionPremiumOnly,
        streaming_enabled: streaming,
        scheduling_enabled: scheduling,
        welcome_message: welcome,
        brand_name: brandName,
        brand_tagline: brandTagline,
      });
      setVoice(res.voice_enabled);
      setRolesEnabled(res.user_roles_enabled);
      setPaused(res.generation_paused);
      setMaxTokens(String(res.max_tokens));
      setVision(res.vision_enabled);
      setVisionSel(`${res.vision_provider}:${res.vision_model}`);
      setVisionPremiumOnly(res.vision_premium_only);
      setStreaming(res.streaming_enabled);
      setScheduling(res.scheduling_enabled);
      setWelcome(res.welcome_message);
      setBrandName(res.brand_name);
      setBrandTagline(res.brand_tagline);
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
    <div className="space-y-3">
      {/* Availability — the global kill-switch lives alone so it's unmissable. */}
      <Card>
        <SectionTitle icon={Power}>Availability</SectionTitle>
        <ToggleRow
          icon={PauseCircle}
          title="Pause bot"
          desc="Kill-switch — stops generating replies for everyone."
          checked={paused}
          onChange={setPaused}
          label="Pause bot"
          tone="danger"
        />
        {paused && (
          <p className="mt-2 text-xs font-medium text-red-500">
            Bot is paused — users get a maintenance message.
          </p>
        )}
      </Card>

      {/* Features — what users can do. */}
      <Card>
        <SectionTitle icon={Sparkles}>Features</SectionTitle>
        <div className="space-y-2">
          <ToggleRow
            icon={Mic}
            title="Voice transcription"
            desc="Transcribe incoming voice messages."
            checked={voice}
            onChange={setVoice}
            label="Voice transcription"
          />
          <ToggleRow
            icon={Drama}
            title="Personal roles"
            desc="Let users define their own assistant role in Settings."
            checked={rolesEnabled}
            onChange={setRolesEnabled}
            label="Allow personal roles"
          />
          <ToggleRow
            icon={AlarmClock}
            title="Scheduled reminders"
            desc="Let users create recurring reminders the bot sends in their local time."
            checked={scheduling}
            onChange={setScheduling}
            label="Scheduled reminders"
          />

          {/* Vision — toggle plus its nested options when enabled. */}
          <div className="rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <ImageIcon className="h-5 w-5" aria-hidden />
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-text">
                  Image understanding (vision)
                </p>
                <p className="text-xs text-muted">
                  Let users send photos (e.g. count calories from a meal).
                </p>
              </div>
              <Toggle checked={vision} onChange={setVision} label="Vision" />
            </div>
            {vision && (
              <div className="mt-3 space-y-3 border-t border-border pt-3">
                <div className="flex items-center gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-text">Premium only</p>
                    <p className="text-xs text-muted">
                      Free users get an upsell instead — no request is used.
                    </p>
                  </div>
                  <Toggle
                    checked={visionPremiumOnly}
                    onChange={setVisionPremiumOnly}
                    label="Vision premium only"
                  />
                </div>
                <div>
                  <Field label="Vision model — which AI reads the photos">
                    <Select
                      options={visionOptions}
                      value={visionSel}
                      onChange={setVisionSel}
                      placeholder="Pick a model…"
                    />
                  </Field>
                  <p className="mt-1 text-xs text-muted">
                    Pick a vision-capable model (e.g. GPT-4o, Gemini). If it&rsquo;s
                    busy, the bot falls back to the user&rsquo;s other models
                    automatically.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Generation — cost/length controls. */}
      <Card>
        <SectionTitle icon={SlidersHorizontal}>Generation</SectionTitle>
        <div className="mb-2">
          <ToggleRow
            icon={Zap}
            title="Stream replies"
            desc="Show the answer live, word by word, as it's generated."
            checked={streaming}
            onChange={setStreaming}
            label="Stream replies"
          />
        </div>
        <div className="flex items-center gap-3 rounded-2xl border border-border bg-surface-2/50 px-3.5 py-3">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-text">Max tokens per reply</p>
            <p className="text-xs text-muted">
              Caps response length to control cost. 0 = provider default.
            </p>
          </div>
          <input
            type="number"
            inputMode="numeric"
            min={0}
            step={1}
            value={maxTokens}
            onChange={(e) => setMaxTokens(e.target.value)}
            aria-label="Max tokens per reply"
            placeholder="0"
            className="w-24 rounded-xl border border-border bg-surface-2/60 px-2.5 py-2 text-right text-sm text-text outline-none transition focus:border-primary focus:shadow-ring"
          />
        </div>
      </Card>

      {/* Welcome message. */}
      <Card>
        <SectionTitle icon={MessageSquareText}>Welcome message</SectionTitle>
        <p className="mb-2 text-xs text-muted">
          Sent on /start. Use <code>{"{name}"}</code> for the user&rsquo;s name.
          Leave empty for the default.
        </p>
        <textarea
          value={welcome}
          onChange={(e) => setWelcome(e.target.value)}
          rows={4}
          placeholder="👋 Hi {name}! I'm your assistant…"
          className="w-full resize-y rounded-2xl border border-border bg-surface-2/60 p-3 text-sm text-text outline-none transition focus:border-primary focus:bg-surface focus:shadow-ring"
        />
      </Card>

      {/* Branding. */}
      <Card>
        <SectionTitle icon={BadgeCheck}>Branding</SectionTitle>
        <p className="mb-3 text-xs text-muted">Shown in the app header.</p>
        <div className="space-y-3">
          <Field label="Brand name">
            <Input
              value={brandName}
              onChange={(e) => setBrandName(e.target.value)}
              placeholder="GetMem"
              aria-label="Brand name"
            />
          </Field>
          <Field label="Tagline">
            <Input
              value={brandTagline}
              onChange={(e) => setBrandTagline(e.target.value)}
              placeholder="Memory-first assistant"
              aria-label="Brand tagline"
            />
          </Field>
        </div>
      </Card>

      {/* Models in rotation. */}
      <Card>
        <SectionTitle icon={Layers}>Models in rotation</SectionTitle>
        <p className="mb-3 text-xs text-muted">
          Turn a model off to drop it from the rotation pool for everyone.
        </p>
        {initial.all_models.length === 0 ? (
          <p className="text-xs text-muted">No models configured.</p>
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
                      className={`truncate text-sm ${off ? "text-muted line-through" : "text-text"}`}
                    >
                      {m.label}
                    </p>
                    <p className="truncate text-xs text-muted">{m.id}</p>
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
      </Card>

      {/* One save bar for the whole screen, pinned so it's always reachable. */}
      <div className="sticky bottom-3 z-10 flex items-center justify-between gap-3 rounded-2xl border border-border bg-surface/90 px-4 py-3 shadow-pop backdrop-blur">
        <SaveMessage status={status} message={message} />
        <Button onClick={save} disabled={status === "saving"} icon={Save} size="sm">
          {status === "saving" ? "Saving…" : "Save"}
        </Button>
      </div>
    </div>
  );
}
