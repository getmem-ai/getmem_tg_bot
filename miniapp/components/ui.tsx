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
    "inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100";
  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2.5 text-sm",
  };
  const variants = {
    primary: "bg-tg-button text-tg-button-text shadow-sm",
    secondary:
      "bg-tg-bg/60 text-tg-text border border-black/[0.08] dark:border-white/[0.12]",
    ghost: "text-tg-button hover:bg-tg-button/10",
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
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = "",
}: SegmentedControlProps<T>) {
  return (
    <div
      className={`flex gap-1 rounded-xl bg-tg-bg/50 p-1 border border-black/[0.06] dark:border-white/[0.08] ${className}`}
      role="tablist"
    >
      {options.map((opt) => {
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
            className={`flex flex-1 items-center justify-center gap-1.5 rounded-lg px-2 py-1.5 text-xs font-medium transition ${
              active
                ? "bg-tg-button text-tg-button-text shadow-sm"
                : "text-tg-hint active:bg-black/[0.04] dark:active:bg-white/[0.06]"
            }`}
          >
            {Icon && <Icon className="h-3.5 w-3.5" aria-hidden />}
            {opt.label}
          </button>
        );
      })}
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
        checked ? "bg-tg-button" : "bg-tg-hint/30"
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
      ? "text-green-500"
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
    <div className="flex flex-col items-center justify-center py-8 text-center">
      {Icon && (
        <span className="mb-2 flex h-11 w-11 items-center justify-center rounded-2xl bg-tg-hint/10 text-tg-hint">
          <Icon className="h-5 w-5" aria-hidden />
        </span>
      )}
      <p className="text-sm font-medium text-tg-text">{title}</p>
      {hint && <p className="mt-1 max-w-[16rem] text-xs text-tg-hint">{hint}</p>}
    </div>
  );
}
