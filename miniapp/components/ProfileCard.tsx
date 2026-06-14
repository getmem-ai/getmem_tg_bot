import { useState } from "react";
import { Crown, Cpu, CalendarClock, Globe, Pencil, Sparkles } from "lucide-react";
import type { TierInfo, User } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { haptic } from "@/lib/telegram";
import { ProfileEditor } from "./ProfileEditor";

interface ProfileCardProps {
  user: User;
  tier?: TierInfo;
  /** When provided and the user is on the free plan, shows an Upgrade button. */
  onUpgrade?: () => void;
  /** Called after the user saves profile changes (to refresh /me). */
  onProfileSaved?: () => void;
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
    <div className="flex items-center gap-2 text-[13px] text-white/80">
      <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
      <span>{label}</span>
      <span className="ml-auto truncate font-semibold text-white">{value}</span>
    </div>
  );
}

export function ProfileCard({
  user,
  tier,
  onUpgrade,
  onProfileSaved,
}: ProfileCardProps) {
  const isPremium = user.is_premium || user.tier === "premium";
  const model = user.preferred_model ?? "Auto";
  const showUpgrade = !isPremium && onUpgrade;
  const initial =
    user.first_name?.trim()?.[0] || user.username?.trim()?.[0] || "U";
  const [editing, setEditing] = useState(false);

  return (
    <section className="relative overflow-hidden rounded-card-lg bg-grad-profile p-4 text-white shadow-pop">
      {/* Soft decorative glows for depth (no heavy photo background) */}
      <div
        aria-hidden
        className="pointer-events-none absolute -right-12 -top-14 h-44 w-44 rounded-full bg-white/15 blur-2xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-16 -left-10 h-44 w-44 rounded-full bg-accent/25 blur-3xl"
      />

      {/* Edit profile */}
      <button
        type="button"
        onClick={() => {
          haptic("light");
          setEditing(true);
        }}
        aria-label="Edit profile"
        className="absolute right-3 top-3 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/15 text-white backdrop-blur transition active:scale-95 active:bg-white/25"
      >
        <Pencil className="h-4 w-4" aria-hidden />
      </button>

      <div className="relative flex items-center gap-3">
        <button
          type="button"
          onClick={() => {
            haptic("light");
            setEditing(true);
          }}
          aria-label="Edit profile photo"
          className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-white/15 text-xl font-bold uppercase text-white shadow-soft ring-1 ring-white/40 backdrop-blur transition active:scale-95"
        >
          {user.avatar ? (
            // Stored data URL — next/image isn't needed here.
            // eslint-disable-next-line @next/next/no-img-element
            <img src={user.avatar} alt="" className="h-full w-full object-cover" />
          ) : (
            initial
          )}
        </button>
        <div className="min-w-0 flex-1 pr-9">
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

      <div className="relative mt-3 grid grid-cols-1 gap-1.5 rounded-2xl bg-white/10 p-3 backdrop-blur">
        <HeroRow icon={Cpu} label="Model" value={model} />
        <HeroRow icon={Globe} label="Timezone" value={user.timezone} />
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
          className="relative mt-3 flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-2.5 text-sm font-semibold text-brand-700 shadow-soft transition active:scale-[0.99]"
        >
          <Sparkles className="h-4 w-4" aria-hidden />
          Upgrade to Premium
        </button>
      )}

      {editing && (
        <ProfileEditor
          user={user}
          onClose={() => setEditing(false)}
          onSaved={() => onProfileSaved?.()}
        />
      )}
    </section>
  );
}
