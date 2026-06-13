import type { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
}

/** A rounded, subtly bordered surface that adapts to the Telegram theme. */
export function Card({ children, className = "" }: CardProps) {
  return (
    <section
      className={`rounded-card border border-black/[0.06] dark:border-white/[0.08] bg-tg-secondary/50 p-4 ${className}`}
    >
      {children}
    </section>
  );
}

interface SectionTitleProps {
  children: ReactNode;
  right?: ReactNode;
}

export function SectionTitle({ children, right }: SectionTitleProps) {
  return (
    <div className="flex items-center justify-between mb-3">
      <h2 className="text-xs font-semibold uppercase tracking-wide text-tg-hint">
        {children}
      </h2>
      {right}
    </div>
  );
}
