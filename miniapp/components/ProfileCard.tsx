import { Crown, Cpu, CalendarClock, Sparkles } from "lucide-react";
import type { TierInfo, User } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { haptic } from "@/lib/telegram";
import { Card } from "./Card";

interface ProfileCardProps {
  user: User;
  tier?: TierInfo;
  /** When provided and the user is on the free plan, shows an Upgrade button. */
  onUpgrade?: () => void;
}

function TierBadge({ user }: { user: User }) {
  const isPremium = user.is_premium || user.tier === "premium";
  if (isPremium) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-400/15 px-2.5 py-0.5 text-xs font-semibold text-amber-500">
        <Crown className="h-3 w-3" aria-hidden /> Premium
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-tg-hint/15 px-2.5 py-0.5 text-xs font-semibold text-tg-hint">
      Free
    </span>
  );
}

export function ProfileCard({ user, tier, onUpgrade }: ProfileCardProps) {
  const isPremium = user.is_premium || user.tier === "premium";
  const initial = (user.first_name || "?").charAt(0).toUpperCase();
  const model = user.preferred_model ?? "Auto";
  const showUpgrade = !isPremium && onUpgrade;

  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-tg-button to-tg-button/70 text-xl font-bold text-tg-button-text shadow-sm">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-lg font-bold">{user.first_name}</p>
            <TierBadge user={user} />
          </div>
          {user.username ? (
            <p className="truncate text-sm text-tg-hint">@{user.username}</p>
          ) : (
            <p className="truncate text-sm text-tg-hint">
              Member since {formatDate(user.created_at)}
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-2 border-t border-black/[0.05] dark:border-white/[0.07] pt-3 text-sm">
        <div className="flex items-center gap-2 text-tg-hint">
          <Cpu className="h-4 w-4 shrink-0" aria-hidden />
          <span>Model</span>
          <span className="ml-auto truncate font-medium text-tg-text">{model}</span>
        </div>
        {tier && (
          <div className="flex items-center gap-2 text-tg-hint">
            <Crown className="h-4 w-4 shrink-0" aria-hidden />
            <span>Plan</span>
            <span className="ml-auto font-medium text-tg-text">
              {tier.name} · {tier.daily_limit}/day
            </span>
          </div>
        )}
        {isPremium && user.premium_until && (
          <div className="flex items-center gap-2 text-tg-hint">
            <CalendarClock className="h-4 w-4 shrink-0" aria-hidden />
            <span>Premium until</span>
            <span className="ml-auto font-medium text-tg-text">
              {formatDate(user.premium_until)}
            </span>
          </div>
        )}
      </div>

      {showUpgrade && (
        <button
          onClick={() => {
            haptic("medium");
            onUpgrade?.();
          }}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-amber-500 to-amber-400 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition active:scale-[0.99]"
        >
          <Sparkles className="h-4 w-4" aria-hidden />
          Upgrade to Premium
        </button>
      )}
    </Card>
  );
}
