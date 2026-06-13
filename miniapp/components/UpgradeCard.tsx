"use client";

import { Crown, Sparkles, Zap } from "lucide-react";
import { openBot } from "@/lib/telegram";
import { Button } from "./ui";

// Optional deep link to the bot's /upgrade command. If a bot username is
// configured at build time we deep-link to it; otherwise openBot() falls back
// to simply closing the mini app so the user returns to the chat.
const BOT_USERNAME = process.env.NEXT_PUBLIC_BOT_USERNAME;

const PERKS = [
  "Much higher daily message limit",
  "Access to premium models",
  "Priority during busy times",
];

/** Call-to-action shown to free users. Payment happens in the bot via Stars. */
export function UpgradeCard() {
  function handleUpgrade() {
    const url = BOT_USERNAME
      ? `https://t.me/${BOT_USERNAME}?start=upgrade`
      : undefined;
    openBot(url);
  }

  return (
    <div className="relative overflow-hidden rounded-2xl border border-amber-400/30 bg-gradient-to-br from-amber-400/10 to-amber-500/[0.04] p-5 shadow-sm">
      <div className="absolute -right-6 -top-6 text-amber-400/20" aria-hidden>
        <Crown className="h-28 w-28" />
      </div>

      <div className="relative">
        <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-400/20 px-2.5 py-1 text-xs font-semibold text-amber-500">
          <Sparkles className="h-3.5 w-3.5" aria-hidden /> Premium
        </span>
        <h3 className="mt-3 text-lg font-bold">Upgrade to Premium</h3>
        <p className="mt-1 text-sm text-tg-hint">
          Unlock more messages and better models with Telegram Stars.
        </p>

        <ul className="mt-3 space-y-1.5">
          {PERKS.map((perk) => (
            <li key={perk} className="flex items-center gap-2 text-sm text-tg-text">
              <Zap className="h-4 w-4 shrink-0 text-amber-500" aria-hidden />
              {perk}
            </li>
          ))}
        </ul>

        <Button onClick={handleUpgrade} icon={Crown} full className="mt-4">
          Upgrade in the bot
        </Button>
        <p className="mt-2 text-center text-[11px] text-tg-hint">
          Opens the bot — tap /upgrade to pay with Stars.
        </p>
      </div>
    </div>
  );
}
