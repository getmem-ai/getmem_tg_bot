import { Crown, Cpu, CalendarClock, Sparkles } from "lucide-react";
import type { TierInfo, User } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { haptic } from "@/lib/telegram";

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
      <span className="inline-flex items-center gap-1 rounded-full bg-white/20 px-2.5 py-1 text-xs font-semibold text-white backdrop-blur">
        <Crown className="h-3 w-3" aria-hidden /> Premium
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-xs font-semibold text-white/90 backdrop-blur">
      Free
    </span>
  );
}

/** A row inside the hero's frosted detail panel. */
function HeroRow({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Cpu;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2 text-sm text-white/75">
      <Icon className="h-4 w-4 shrink-0" aria-hidden />
      <span>{label}</span>
      <span className="ml-auto truncate font-semibold text-white">{value}</span>
    </div>
  );
}

export function ProfileCard({ user, tier, onUpgrade }: ProfileCardProps) {
  const isPremium = user.is_premium || user.tier === "premium";
  const initial = (user.first_name || "?").charAt(0).toUpperCase();
  const model = user.preferred_model ?? "Auto";
  const showUpgrade = !isPremium && onUpgrade;

  return (
    <section className="relative overflow-hidden rounded-card-lg bg-hero p-5 text-white shadow-pop">
      {/* Soft decorative glow */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-10 -top-12 h-40 w-40 rounded-full bg-white/15 blur-2xl"
      />

      <div className="relative flex items-center gap-4">
        <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-white/20 text-2xl font-bold text-white shadow-inner backdrop-blur">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-xl font-bold">{user.first_name}</p>
            <TierBadge user={user} />
          </div>
          {user.username ? (
            <p className="truncate text-sm text-white/70">@{user.username}</p>
          ) : (
            <p className="truncate text-sm text-white/70">
              Member since {formatDate(user.created_at)}
            </p>
          )}
        </div>
      </div>

      <div className="relative mt-4 grid grid-cols-1 gap-2.5 rounded-2xl bg-white/10 p-4 backdrop-blur">
        <HeroRow icon={Cpu} label="Model" value={model} />
        {tier && (
          <HeroRow
            icon={Crown}
            label="Plan"
            value={`${tier.name} · ${tier.daily_limit}/day`}
          />
        )}
        {isPremium && user.premium_until && (
          <HeroRow
            icon={CalendarClock}
            label="Premium until"
            value={formatDate(user.premium_until)}
          />
        )}
      </div>

      {showUpgrade && (
        <button
          onClick={() => {
            haptic("medium");
            onUpgrade?.();
          }}
          className="relative mt-4 flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-brand-700 shadow-soft transition active:scale-[0.99]"
        >
          <Sparkles className="h-4 w-4" aria-hidden />
          Upgrade to Premium
        </button>
      )}
    </section>
  );
}
