import type { CSSProperties } from "react";

interface SkeletonProps {
  className?: string;
  style?: CSSProperties;
}

/** A shimmering placeholder block. Uses the `.skeleton` style from globals.css. */
export function Skeleton({ className = "", style }: SkeletonProps) {
  return (
    <div
      className={`skeleton rounded-md ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

/** A reusable card-shaped skeleton with a few placeholder lines. */
export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="rounded-card border border-black/[0.04] dark:border-white/[0.06] p-5 bg-tg-bg shadow-card">
      <Skeleton className="h-4 w-1/3 mb-3" />
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className="h-3" style={{ width: `${90 - i * 12}%` }} />
        ))}
      </div>
    </div>
  );
}
