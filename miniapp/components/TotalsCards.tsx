import type { Totals } from "@/lib/types";
import { formatNumber } from "@/lib/format";

interface TotalsCardsProps {
  totals: Totals;
}

interface StatProps {
  label: string;
  value: number;
  icon: string;
}

function Stat({ label, value, icon }: StatProps) {
  return (
    <div className="flex-1 rounded-card border border-black/[0.06] dark:border-white/[0.08] bg-tg-secondary/50 p-4">
      <div className="text-xl" aria-hidden>
        {icon}
      </div>
      <div className="mt-2 text-2xl font-bold leading-none">
        {formatNumber(value)}
      </div>
      <div className="mt-1 text-xs text-tg-hint">{label}</div>
    </div>
  );
}

export function TotalsCards({ totals }: TotalsCardsProps) {
  return (
    <div className="flex gap-3">
      <Stat label="Messages" value={totals.messages} icon="💬" />
      <Stat label="Payments" value={totals.payments} icon="💳" />
    </div>
  );
}
