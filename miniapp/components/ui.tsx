"use client";

import {
  useEffect,
  useId,
  useRef,
  useState,
  type ComponentType,
  type ReactNode,
} from "react";
import { Check, ChevronDown } from "lucide-react";
import { haptic, hapticSelection } from "@/lib/telegram";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

interface ButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "ghost" | "accent" | "danger";
  size?: "sm" | "md";
  full?: boolean;
  icon?: IconType;
  className?: string;
  type?: "button" | "submit";
}

const BUTTON_VARIANTS: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary: "bg-grad-primary text-primary-fg shadow-pop",
  accent: "bg-grad-accent text-accent-fg shadow-pop",
  secondary: "bg-surface-2 text-text border border-border",
  ghost: "text-primary hover:bg-primary/10",
  danger: "bg-danger/12 text-danger",
};

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
    "inline-flex items-center justify-center gap-2 rounded-2xl font-semibold transition active:scale-[0.98] disabled:opacity-50 disabled:active:scale-100 focus-visible:outline-none focus-visible:shadow-ring";
  const sizes = { sm: "px-3.5 py-2 text-xs", md: "px-4 py-2.5 text-sm" };
  return (
    <button
      type={type}
      onClick={() => {
        if (disabled) return;
        haptic("light");
        onClick?.();
      }}
      disabled={disabled}
      className={`${base} ${sizes[size]} ${BUTTON_VARIANTS[variant]} ${full ? "w-full" : ""} ${className}`}
    >
      {Icon && <Icon className="h-4 w-4" aria-hidden />}
      {children}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Field + Input (consistent form controls)
// ---------------------------------------------------------------------------

export const inputClass =
  "w-full rounded-2xl border border-border bg-surface-2/60 px-3.5 py-2.5 text-sm text-text outline-none transition placeholder:text-muted focus:border-primary focus:bg-surface focus:shadow-ring disabled:opacity-50";

export function Field({
  label,
  hint,
  children,
}: {
  label?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <label className="block">
      {label && (
        <span className="mb-1.5 block text-[11px] font-semibold uppercase tracking-wide text-muted">
          {label}
        </span>
      )}
      {children}
      {hint && <span className="mt-1 block text-xs text-muted">{hint}</span>}
    </label>
  );
}

export function Input(
  props: React.InputHTMLAttributes<HTMLInputElement> & { className?: string },
) {
  const { className = "", ...rest } = props;
  return <input className={`${inputClass} ${className}`} {...rest} />;
}

// ---------------------------------------------------------------------------
// Select (custom dropdown — replaces native <select>)
// ---------------------------------------------------------------------------

export interface SelectOption<T extends string> {
  value: T;
  label: string;
  hint?: string;
}

interface SelectProps<T extends string> {
  options: ReadonlyArray<SelectOption<T>>;
  value: T;
  onChange: (value: T) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function Select<T extends string>({
  options,
  value,
  onChange,
  placeholder = "Select…",
  disabled,
  className = "",
}: SelectProps<T>) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const listId = useId();
  const current = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => {
          if (disabled) return;
          hapticSelection();
          setOpen((o) => !o);
        }}
        className={`${inputClass} flex items-center justify-between gap-2 text-left ${open ? "border-primary shadow-ring" : ""}`}
      >
        <span className={current ? "text-text" : "text-muted"}>
          {current?.label ?? placeholder}
        </span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-muted transition ${open ? "rotate-180" : ""}`}
          aria-hidden
        />
      </button>

      {open && (
        <ul
          id={listId}
          role="listbox"
          className="animate-sheet-up absolute z-30 mt-2 max-h-64 w-full overflow-auto rounded-2xl border border-border bg-surface p-1.5 shadow-card"
        >
          {options.map((opt) => {
            const active = opt.value === value;
            return (
              <li key={opt.value} role="option" aria-selected={active}>
                <button
                  type="button"
                  onClick={() => {
                    hapticSelection();
                    onChange(opt.value);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2.5 text-left text-sm transition ${
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-text active:bg-surface-2"
                  }`}
                >
                  <span className="min-w-0">
                    <span className="block truncate font-medium">{opt.label}</span>
                    {opt.hint && (
                      <span className="block truncate text-xs text-muted">{opt.hint}</span>
                    )}
                  </span>
                  {active && <Check className="h-4 w-4 shrink-0" aria-hidden />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Segmented control (white active pill on a soft track — like the references)
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
  scroll?: boolean;
}

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className = "",
  scroll,
}: SegmentedControlProps<T>) {
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
            ? "shrink-0 snap-start whitespace-nowrap px-4 py-2"
            : "flex-1 px-2 py-2"
        } ${
          active
            ? "bg-surface text-primary shadow-soft"
            : "text-muted active:bg-black/[0.03] dark:active:bg-white/[0.05]"
        }`}
      >
        {Icon && <Icon className="h-3.5 w-3.5" aria-hidden />}
        {opt.label}
      </button>
    );
  });

  if (scrollable) {
    return (
      <div className={`relative ${className}`}>
        <div
          role="tablist"
          className="no-scrollbar flex snap-x gap-1 overflow-x-auto rounded-full bg-surface-2 p-1 [-webkit-overflow-scrolling:touch]"
        >
          {buttons}
        </div>
        <div
          aria-hidden
          className="pointer-events-none absolute inset-y-1 right-1 w-8 rounded-r-full bg-gradient-to-l from-bg/90 to-transparent"
        />
      </div>
    );
  }

  return (
    <div
      className={`flex gap-1 rounded-full bg-surface-2 p-1 ${className}`}
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
        checked ? "bg-primary" : "bg-muted/35"
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
// Badge / chip
// ---------------------------------------------------------------------------

export function Badge({
  children,
  tone = "neutral",
  icon: Icon,
}: {
  children: ReactNode;
  tone?: "neutral" | "primary" | "accent" | "success" | "danger";
  icon?: IconType;
}) {
  const tones = {
    neutral: "bg-surface-2 text-muted",
    primary: "bg-primary/12 text-primary",
    accent: "bg-accent/15 text-accent-600",
    success: "bg-success/12 text-success",
    danger: "bg-danger/12 text-danger",
  };
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${tones[tone]}`}
    >
      {Icon && <Icon className="h-3 w-3" aria-hidden />}
      {children}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Inline save status
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
      ? "text-success"
      : status === "error"
        ? "text-danger"
        : "text-muted";
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
        <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Icon className="h-5 w-5" aria-hidden />
        </span>
      )}
      <p className="text-sm font-semibold text-text">{title}</p>
      {hint && (
        <p className="mt-1.5 max-w-[16rem] text-xs leading-relaxed text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
