import type { ComponentType } from "react";
import { CreditCard, MessageSquare } from "lucide-react";
import type { Totals } from "@/lib/types";
import { formatNumber } from "@/lib/format";

type IconType = ComponentType<{ className?: string; "aria-hidden"?: boolean }>;

interface TotalsCardsProps {
  totals: Totals;
}

function Stat({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: number;
  icon: IconType;
}) {
  return (
    <div className="flex-1 rounded-card border border-black/[0.04] dark:border-white/[0.06] bg-tg-bg p-5 shadow-card">
      <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-brand/10 text-brand">
        <Icon className="h-5 w-5" aria-hidden />
      </span>
      <div className="mt-3 text-2xl font-bold leading-none tabular-nums">
        {formatNumber(value)}
      </div>
      <div className="mt-1.5 text-xs text-tg-hint">{label}</div>
    </div>
  );
}

export function TotalsCards({ totals }: TotalsCardsProps) {
  return (
    <div className="flex gap-3">
      <Stat label="Messages" value={totals.messages} icon={MessageSquare} />
      <Stat label="Payments" value={totals.payments} icon={CreditCard} />
    </div>
  );
}
