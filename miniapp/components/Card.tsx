import type { ComponentType, ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

/** A rounded, subtly bordered surface that adapts to the Telegram theme. */
export function Card({ children, className = "" }: CardProps) {
  return (
    <section
      className={`rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-secondary/50 p-4 shadow-sm shadow-black/[0.02] ${className}`}
    >
      {children}
    </section>
  );
}

interface SectionTitleProps {
  children: ReactNode;
  right?: ReactNode;
  icon?: ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
}

export function SectionTitle({ children, right, icon: Icon }: SectionTitleProps) {
  return (
    <div className="mb-3 flex items-center justify-between gap-3">
      <h2 className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-tg-hint">
        {Icon && <Icon className="h-3.5 w-3.5" aria-hidden />}
        {children}
      </h2>
      {right}
    </div>
  );
}

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: ComponentType<{ className?: string; "aria-hidden"?: boolean }>;
  right?: ReactNode;
}

/** A consistent page header used at the top of each tab. */
export function PageHeader({ title, subtitle, icon: Icon, right }: PageHeaderProps) {
  return (
    <header className="mb-1 flex items-center justify-between gap-3">
      <div className="flex items-center gap-2.5 min-w-0">
        {Icon && (
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-tg-button/10 text-tg-button">
            <Icon className="h-5 w-5" aria-hidden />
          </span>
        )}
        <div className="min-w-0">
          <h1 className="truncate text-xl font-bold leading-tight">{title}</h1>
          {subtitle && (
            <p className="truncate text-xs text-tg-hint">{subtitle}</p>
          )}
        </div>
      </div>
      {right}
    </header>
  );
}
