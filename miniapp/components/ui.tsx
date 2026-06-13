"use client";

import type { ComponentType, ReactNode } from "react";
import { Check } from "lucide-react";
import { haptic, hapticSelection } from "@/lib/telegram";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
  full?: boolean;
  icon?: IconType;
  className?: string;
  type?: "button" | "submit";
}

export function Button({
  children,
  onClick,
  disabled,
  variant = "primary",
  size = "md",
  full,
  icon: Icon,
  className = "",
  type = "button",
}: ButtonProps) {
  const base =
    "inline-flex items-center justify-center gap-2 rounded-2xl font-semibold transition active:scale-[0.99] disabled:opacity-50 disabled:active:scale-100";
  const sizes = {
    sm: "px-3.5 py-2 text-xs",
    md: "px-4 py-2.5 text-sm",
  };
  const variants = {
    primary: "bg-brand text-brand-fg shadow-pop",
    secondary:
      "bg-tg-secondary text-tg-text border border-black/[0.04] dark:border-white/[0.06]",
    ghost: "text-brand hover:bg-brand/10",
  };
  return (
    <button
      type={type}
      onClick={() => {
        if (disabled) return;
        haptic("light");
        onClick?.();
      }}
      disabled={disabled}
      className={`${base} ${sizes[size]} ${variants[variant]} ${full ? "w-full" : ""} ${className}`}
    >
      {Icon && <Icon className="h-4 w-4" aria-hidden />}
      {children}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Segmented control
// ---------------------------------------------------------------------------

export interface SegmentOption<T extends string> {
  value: T;
  label: string;
  icon?: IconType;
}

interface SegmentedControlProps<T extends string> {
  options: ReadonlyArray<SegmentOption<T>>;
  value: T;
  onChange: (value: T) => void;
  className?: string;
  /**
   * When true (or auto-enabled for >3 options) the control becomes a single
   * horizontally-scrollable row of pills instead of an evenly-divided segmented
   * control. Use for navigation strips that can't fit on a narrow screen.
   */
  scroll?: boolean;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = "",
  scroll,
}: SegmentedControlProps<T>) {
  // Degrade gracefully: a segmented control with too many items would clip on a
  // phone, so switch to a scrollable strip automatically past 3 items.
  const scrollable = scroll ?? options.length > 3;

  const buttons = options.map((opt) => {
    const active = opt.value === value;
    const Icon = opt.icon;
    return (
      <button
        key={opt.value}
        role="tab"
        aria-selected={active}
        onClick={() => {
          hapticSelection();
          onChange(opt.value);
        }}
        className={`flex items-center justify-center gap-1.5 rounded-full text-xs font-semibold transition ${
          scrollable
            ? "shrink-0 snap-start whitespace-nowrap px-3.5 py-2"
            : "flex-1 px-2 py-2"
        } ${
          active
            ? "bg-brand text-brand-fg shadow-soft"
            : "text-tg-hint active:bg-black/[0.04] dark:active:bg-white/[0.06]"
        }`}
      >
        {Icon && <Icon className="h-3.5 w-3.5" aria-hidden />}
        {opt.label}
      </button>
    );
  });

  if (scrollable) {
    return (
      // The wrapper clips the rounded corners and hosts a right-edge fade that
      // hints there are more items off-screen.
      <div className={`relative ${className}`}>
        <div
          role="tablist"
          className="no-scrollbar flex snap-x gap-1 overflow-x-auto rounded-full bg-tg-secondary p-1 [-webkit-overflow-scrolling:touch]"
        >
          {buttons}
        </div>
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-1 right-1 w-8 rounded-r-full bg-gradient-to-l from-tg-bg/80 to-transparent"
        />
      </div>
    );
  }

  return (
    <div
      className={`flex gap-1 rounded-full bg-tg-secondary p-1 ${className}`}
      role="tablist"
    >
      {buttons}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Toggle (switch)
// ---------------------------------------------------------------------------

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  label?: string;
}

export function Toggle({ checked, onChange, disabled, label }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => {
        if (disabled) return;
        haptic("light");
        onChange(!checked);
      }}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition disabled:opacity-50 ${
        checked ? "bg-brand shadow-soft" : "bg-tg-hint/30"
      }`}
    >
      <span
        className={`inline-block h-5 w-5 transform rounded-full bg-white shadow transition ${
          checked ? "translate-x-[22px]" : "translate-x-0.5"
        }`}
      />
    </button>
  );
}

// ---------------------------------------------------------------------------
// Inline save status (text next to a Save button)
// ---------------------------------------------------------------------------

export type SaveStatus = "idle" | "saving" | "saved" | "error";

export function SaveMessage({
  status,
  message,
}: {
  status: SaveStatus;
  message: string;
}) {
  if (!message) return null;
  const tone =
    status === "saved"
      ? "text-emerald-500"
      : status === "error"
        ? "text-red-500"
        : "text-tg-hint";
  return (
    <span className={`flex items-center gap-1 text-xs ${tone}`}>
      {status === "saved" && <Check className="h-3.5 w-3.5" aria-hidden />}
      {message}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

export function EmptyState({
  icon: Icon,
  title,
  hint,
}: {
  icon?: IconType;
  title: string;
  hint?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-10 text-center">
      {Icon && (
        <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-brand/10 text-brand">
          <Icon className="h-5 w-5" aria-hidden />
        </span>
      )}
      <p className="text-sm font-semibold text-tg-text">{title}</p>
      {hint && <p className="mt-1.5 max-w-[16rem] text-xs leading-relaxed text-tg-hint">{hint}</p>}
    </div>
  );
}
