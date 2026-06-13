import type { Usage } from "@/lib/types";
import { Card, SectionTitle } from "./Card";

interface UsageRingProps {
  usage: Usage;
}

/** A circular usage ring (SVG) showing used_today / limit. */
export function UsageRing({ usage }: UsageRingProps) {
  const limit = Math.max(usage.limit, 0);
  const used = Math.max(usage.used_today, 0);
  const remaining = Math.max(usage.remaining, 0);

  const ratio = limit > 0 ? Math.min(used / limit, 1) : 0;
  const size = 92;
  const stroke = 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const dash = circumference * ratio;

  const atLimit = limit > 0 && remaining <= 0;
  const ringColor = atLimit ? "#ef4444" : "var(--tg-button)";

  return (
    <Card>
      <SectionTitle>Today&apos;s usage</SectionTitle>
      <div className="flex items-center gap-4">
        <div className="relative shrink-0" style={{ width: size, height: size }}>
          <svg width={size} height={size} className="-rotate-90">
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke="var(--tg-hint)"
              strokeOpacity={0.18}
              strokeWidth={stroke}
            />
            <circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={ringColor}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={`${dash} ${circumference}`}
              style={{ transition: "stroke-dasharray 0.5s ease" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-lg font-bold leading-none">{used}</span>
            <span className="text-[11px] text-tg-hint">/ {limit}</span>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          {atLimit ? (
            <p className="text-sm font-medium text-red-500">
              Limit reached — upgrade in the bot
            </p>
          ) : (
            <p className="text-sm">
              <span className="text-2xl font-bold">{remaining}</span>{" "}
              <span className="text-tg-hint">messages left today</span>
            </p>
          )}
          <p className="mt-1 text-xs text-tg-hint">
            Resets daily. {used} used of {limit}.
          </p>
        </div>
      </div>
    </Card>
  );
}
