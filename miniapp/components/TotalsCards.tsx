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
    <div className="flex-1 rounded-2xl border border-black/[0.06] dark:border-white/[0.08] bg-tg-secondary/50 p-4 shadow-sm shadow-black/[0.02]">
      <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-tg-button/10 text-tg-button">
        <Icon className="h-4 w-4" aria-hidden />
      </span>
      <div className="mt-2.5 text-2xl font-bold leading-none">
        {formatNumber(value)}
      </div>
      <div className="mt-1 text-xs text-tg-hint">{label}</div>
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
