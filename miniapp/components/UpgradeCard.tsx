"use client";

import Image from "next/image";
import { useState } from "react";
import { Check, ChevronDown, Crown, Loader2, Star } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { haptic, openBot, openInvoice } from "@/lib/telegram";
import type { UpgradeTier } from "@/lib/types";
import { formatNumber } from "@/lib/format";

const BOT_USERNAME = process.env.NEXT_PUBLIC_BOT_USERNAME;

interface UpgradeCardProps {
  tiers: UpgradeTier[];
  onPaid?: () => void;
}

/**
 * Shows the paid plans and lets the user pay **inside** the Mini App via
 * Telegram Stars: we ask the backend for an invoice link, then open Telegram's
 * native invoice sheet. On success we refresh the account. Falls back to opening
 * the bot if the in-app invoice API is unavailable.
 */
export function UpgradeCard({ tiers, onPaid }: UpgradeCardProps) {
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string>("");
  // Which tiers have their model list expanded.
  const [open, setOpen] = useState<Set<string>>(new Set());

  function toggleModels(key: string) {
    haptic("light");
    setOpen((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  if (tiers.length === 0) return null;

  async function buy(tier: UpgradeTier) {
    setError("");
    setPending(tier.key);
    haptic("medium");
    try {
      const { invoice_link } = await api.createInvoice(tier.key);
      const opened = openInvoice(invoice_link, (status) => {
        setPending(null);
        if (status === "paid") {
          haptic("heavy");
          onPaid?.();
        }
      });
      if (!opened) {
        // No in-app invoice bridge — fall back to opening the bot.
        openBot(
          BOT_USERNAME ? `https://t.me/${BOT_USERNAME}?start=upgrade` : undefined,
        );
        setPending(null);
      }
    } catch (err: unknown) {
      setPending(null);
      setError(
        err instanceof ApiError
          ? "Couldn't start payment. Try again."
          : "Network error.",
      );
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {tiers.map((tier) => (
        <div
          key={tier.key}
          className="relative overflow-hidden rounded-card-lg bg-hero p-5 text-white shadow-pop"
        >
          <div
            aria-hidden
            className="pointer-events-none absolute -right-8 -top-10 h-36 w-36 rounded-full bg-white/15 blur-2xl"
          />
          <div className="relative flex items-center justify-between gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/20 px-2.5 py-1 text-[11px] font-semibold text-white backdrop-blur">
              <Crown className="h-3 w-3" aria-hidden /> {tier.name}
            </span>
            <span className="flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-white shadow-soft">
              <Image
                src="/brand/premium.png"
                alt=""
                aria-hidden
                width={56}
                height={56}
                className="h-full w-full object-contain p-1"
              />
            </span>
          </div>

          <ul className="relative mt-4 space-y-2 text-sm text-white/90">
            <li className="flex items-center gap-2">
              <Check className="h-4 w-4 shrink-0 text-white" aria-hidden />
              Up to <b className="text-white">{formatNumber(tier.daily_limit)}</b> messages/day
            </li>
            <li>
              <button
                type="button"
                onClick={() => toggleModels(tier.key)}
                aria-expanded={open.has(tier.key)}
                className="flex w-full items-center gap-2 text-left transition active:scale-[0.99]"
              >
                <Check className="h-4 w-4 shrink-0 text-white" aria-hidden />
                <span>
                  <b className="text-white">{tier.model_count}</b> models incl.
                  premium
                </span>
                {tier.models.length > 0 && (
                  <ChevronDown
                    className={`h-4 w-4 shrink-0 text-white/80 transition-transform ${
                      open.has(tier.key) ? "rotate-180" : ""
                    }`}
                    aria-hidden
                  />
                )}
              </button>
              {open.has(tier.key) && tier.models.length > 0 && (
                <ul className="mt-2 ml-6 flex flex-wrap gap-1.5">
                  {tier.models.map((m) => (
                    <li
                      key={`${m.provider}:${m.id}`}
                      className="rounded-lg bg-white/15 px-2 py-1 text-[12px] font-medium text-white backdrop-blur"
                      title={m.id}
                    >
                      {m.label}
                    </li>
                  ))}
                </ul>
              )}
            </li>
            <li className="flex items-center gap-2">
              <Check className="h-4 w-4 shrink-0 text-white" aria-hidden />
              {tier.period_days} days
            </li>
          </ul>

          <button
            onClick={() => buy(tier)}
            disabled={pending !== null}
            className="relative mt-5 flex w-full items-center justify-center gap-2 rounded-2xl bg-white px-4 py-3 text-sm font-semibold text-brand-700 shadow-soft transition active:scale-[0.99] disabled:opacity-60"
          >
            {pending === tier.key ? (
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            ) : (
              <Star className="h-4 w-4" aria-hidden />
            )}
            Pay {tier.price_stars} Stars
          </button>
        </div>
      ))}

      {error && <p className="px-1 text-xs text-red-500">{error}</p>}
      <p className="px-1 text-center text-[11px] text-tg-hint">
        Secure payment with Telegram Stars.
      </p>
    </div>
  );
}
