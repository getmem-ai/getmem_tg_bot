import type { User } from "@/lib/types";
import { formatDate } from "@/lib/format";
import { Card } from "./Card";

interface ProfileCardProps {
  user: User;
}

function TierBadge({ user }: { user: User }) {
  const isPremium = user.is_premium || user.tier === "premium";
  if (isPremium) {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-amber-400/15 px-2.5 py-0.5 text-xs font-semibold text-amber-500">
        <span aria-hidden>⭐</span> Premium
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-tg-hint/15 px-2.5 py-0.5 text-xs font-semibold text-tg-hint">
      <span aria-hidden>🆓</span> Free
    </span>
  );
}

export function ProfileCard({ user }: ProfileCardProps) {
  const isPremium = user.is_premium || user.tier === "premium";
  const initial = (user.first_name || "?").charAt(0).toUpperCase();
  const model = user.preferred_model ?? "Auto";

  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-tg-button text-lg font-semibold text-tg-button-text">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-base font-semibold">{user.first_name}</p>
            <TierBadge user={user} />
          </div>
          {user.username && (
            <p className="truncate text-sm text-tg-hint">@{user.username}</p>
          )}
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <span className="text-tg-hint">
          Model:{" "}
          <span className="font-medium text-tg-text">{model}</span>
        </span>
        {isPremium && user.premium_until && (
          <span className="text-tg-hint">
            Premium until{" "}
            <span className="font-medium text-tg-text">
              {formatDate(user.premium_until)}
            </span>
          </span>
        )}
      </div>
    </Card>
  );
}
