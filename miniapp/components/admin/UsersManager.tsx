"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Ban,
  Check,
  Crown,
  RotateCcw,
  Save,
  Search,
  Shield,
  ShieldCheck,
  Trash2,
  Users,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { AdminUser, AdminUserUpdate } from "@/lib/types";
import { formatNumber } from "@/lib/format";
import { Card } from "../Card";
import { Skeleton } from "../Skeleton";
import { ErrorState } from "../ErrorState";
import {
  Button,
  EmptyState,
  Field,
  SaveMessage,
  Select,
  type SaveStatus,
} from "../ui";

const PAGE_SIZE = 20;

interface TierOption {
  key: string;
  name: string;
}

function errorMessage(err: unknown): string {
  return err instanceof ApiError && err.isForbidden
    ? "Admins only."
    : "Failed to save.";
}

export function UsersManager() {
  const [search, setSearch] = useState("");
  const [debounced, setDebounced] = useState("");

  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  const [tiers, setTiers] = useState<TierOption[]>([{ key: "free", name: "Free" }]);

  // Debounce the search input (~300ms).
  useEffect(() => {
    const id = window.setTimeout(() => setDebounced(search.trim()), 300);
    return () => window.clearTimeout(id);
  }, [search]);

  // Load tier options once (for the plan dropdown). Always include "free".
  useEffect(() => {
    let cancelled = false;
    api
      .getTiers()
      .then((res) => {
        if (cancelled) return;
        const opts: TierOption[] = [{ key: "free", name: "Free" }];
        for (const t of res.tiers) {
          if (t.key === "free") continue;
          opts.push({ key: t.key, name: t.name });
        }
        setTiers(opts);
      })
      .catch(() => {
        // Non-fatal: fall back to just "free".
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Fetch the first page whenever the debounced search changes.
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .adminListUsers({ search: debounced, limit: PAGE_SIZE, offset: 0 })
      .then((res) => {
        if (cancelled) return;
        setUsers(res.users);
        setTotal(res.total);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err
            : new ApiError(0, "Unknown error", ""),
        );
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debounced]);

  const loadMore = useCallback(async () => {
    setLoadingMore(true);
    try {
      const res = await api.adminListUsers({
        search: debounced,
        limit: PAGE_SIZE,
        offset: users.length,
      });
      setUsers((prev) => [...prev, ...res.users]);
      setTotal(res.total);
    } catch {
      // Keep current list; surface nothing intrusive.
    } finally {
      setLoadingMore(false);
    }
  }, [debounced, users.length]);

  const onUpdated = useCallback((updated: AdminUser) => {
    setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
  }, []);

  const retry = useCallback(() => setDebounced((s) => s), []);

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-tg-hint"
          aria-hidden
        />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by id, @username or name"
          className="w-full rounded-2xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-secondary/60 py-2.5 pl-9 pr-3 text-sm text-tg-text outline-none transition focus:border-brand focus:bg-tg-bg focus:shadow-ring placeholder:text-tg-hint"
        />
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Card key={i}>
              <div className="flex items-center gap-3">
                <Skeleton className="h-9 w-9 rounded-xl" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-1/3" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={retry} />
      ) : users.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No users found"
          hint={debounced ? "Try a different search." : undefined}
        />
      ) : (
        <>
          <div className="space-y-2">
            {users.map((u) => (
              <UserCard
                key={u.id}
                user={u}
                tiers={tiers}
                onUpdated={onUpdated}
              />
            ))}
          </div>

          {users.length < total && (
            <Button
              onClick={loadMore}
              disabled={loadingMore}
              variant="secondary"
              full
              size="sm"
            >
              {loadingMore
                ? "Loading…"
                : `Load more (${formatNumber(total - users.length)})`}
            </Button>
          )}
        </>
      )}
    </div>
  );
}

function UserCard({
  user,
  tiers,
  onUpdated,
}: {
  user: AdminUser;
  tiers: TierOption[];
  onUpdated: (u: AdminUser) => void;
}) {
  const [open, setOpen] = useState(false);
  const initial = (user.first_name || user.username || "?").charAt(0).toUpperCase();
  const tierName =
    tiers.find((t) => t.key === user.tier)?.name ?? user.tier;

  return (
    <Card className="!p-0 overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-3 p-3.5 text-left transition active:bg-black/[0.03] dark:active:bg-white/[0.05]"
      >
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-brand/10 text-sm font-semibold text-brand">
          {initial}
        </span>
        <div className="min-w-0 flex-1">
          <p className="flex items-center gap-1.5 truncate text-sm font-medium text-tg-text">
            <span className="truncate">{user.first_name || "Unknown"}</span>
            {user.is_premium && (
              <Crown className="h-3.5 w-3.5 shrink-0 text-amber-500" aria-hidden />
            )}
            {user.username && (
              <span className="truncate text-xs font-normal text-tg-hint">
                @{user.username}
              </span>
            )}
          </p>
          <p className="mt-0.5 truncate text-xs text-tg-hint">
            Today: {formatNumber(user.used_today)}/{formatNumber(user.daily_limit)} ·{" "}
            {formatNumber(user.messages)} msgs
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <span className="rounded-full bg-brand/12 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand">
            {tierName}
          </span>
          {user.is_admin && (
            <span className="inline-flex items-center gap-0.5 rounded-full bg-brand/12 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-brand">
              <ShieldCheck className="h-3 w-3" aria-hidden /> Admin
            </span>
          )}
          {user.banned && (
            <span className="rounded-md bg-red-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-red-500">
              Banned
            </span>
          )}
        </div>
      </button>

      {open && (
        <UserActions user={user} tiers={tiers} onUpdated={onUpdated} />
      )}
    </Card>
  );
}

const numberFieldClass =
  "w-full rounded-2xl border border-black/[0.08] dark:border-white/[0.1] bg-tg-secondary/60 px-3.5 py-2.5 text-sm text-tg-text outline-none transition focus:border-brand focus:bg-tg-bg focus:shadow-ring disabled:opacity-50";

function UserActions({
  user,
  tiers,
  onUpdated,
}: {
  user: AdminUser;
  tiers: TierOption[];
  onUpdated: (u: AdminUser) => void;
}) {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const [message, setMessage] = useState("");
  const [limitInput, setLimitInput] = useState<string>(
    user.limit_override != null ? String(user.limit_override) : "",
  );
  const savedTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (savedTimer.current) window.clearTimeout(savedTimer.current);
    };
  }, []);

  const flashSaved = useCallback((text = "Saved") => {
    setStatus("saved");
    setMessage(text);
    if (savedTimer.current) window.clearTimeout(savedTimer.current);
    savedTimer.current = window.setTimeout(() => {
      setStatus("idle");
      setMessage("");
    }, 2000);
  }, []);

  const apply = useCallback(
    async (update: AdminUserUpdate, successText?: string) => {
      setStatus("saving");
      setMessage("");
      try {
        const updated = await api.adminUpdateUser(user.id, update);
        onUpdated(updated);
        setLimitInput(
          updated.limit_override != null ? String(updated.limit_override) : "",
        );
        flashSaved(successText);
      } catch (err: unknown) {
        setStatus("error");
        setMessage(errorMessage(err));
      }
    },
    [user.id, onUpdated, flashSaved],
  );

  const saving = status === "saving";

  return (
    <div className="space-y-3 border-t border-black/[0.06] px-3.5 py-3.5 dark:border-white/[0.08]">
      {/* Ban / Unban */}
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-tg-text">Access</span>
        {user.banned ? (
          <Button
            onClick={() => apply({ banned: false }, "Unbanned")}
            disabled={saving}
            variant="secondary"
            size="sm"
            icon={Check}
          >
            Unban
          </Button>
        ) : (
          <button
            type="button"
            onClick={() => apply({ banned: true }, "Banned")}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-red-500/12 px-3 py-1.5 text-xs font-semibold text-red-500 transition active:opacity-80 disabled:opacity-50"
          >
            <Ban className="h-4 w-4" aria-hidden />
            Ban
          </button>
        )}
      </div>

      {/* Admin rights */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <span className="text-sm font-medium text-tg-text">Admin rights</span>
          {user.env_admin && (
            <p className="text-[11px] text-tg-hint">Via ADMIN_IDS — permanent</p>
          )}
        </div>
        {user.env_admin ? (
          <span className="inline-flex items-center gap-1 rounded-2xl bg-brand/12 px-3 py-2 text-xs font-semibold text-brand">
            <ShieldCheck className="h-4 w-4" aria-hidden /> Admin
          </span>
        ) : user.is_admin ? (
          <Button
            onClick={() => apply({ is_admin: false }, "Admin revoked")}
            disabled={saving}
            variant="secondary"
            size="sm"
            icon={Shield}
          >
            Revoke
          </Button>
        ) : (
          <button
            type="button"
            onClick={() => apply({ is_admin: true }, "Admin granted")}
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-2xl bg-brand px-3.5 py-2 text-xs font-semibold text-brand-fg shadow-pop transition active:scale-[0.99] disabled:opacity-50"
          >
            <ShieldCheck className="h-4 w-4" aria-hidden />
            Make admin
          </button>
        )}
      </div>

      {/* Plan */}
      <Field label="Plan">
        <Select
          value={user.tier}
          disabled={saving}
          onChange={(v) => apply({ tier: v }, "Plan updated")}
          options={
            tiers.some((t) => t.key === user.tier)
              ? tiers.map((t) => ({ value: t.key, label: t.name }))
              : [
                  { value: user.tier, label: user.tier },
                  ...tiers.map((t) => ({ value: t.key, label: t.name })),
                ]
          }
        />
      </Field>

      {/* Daily limit override */}
      <div>
        <label className="mb-1 block text-[11px] font-medium text-tg-hint">
          Daily limit override
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            inputMode="numeric"
            min={0}
            value={limitInput}
            disabled={saving}
            onChange={(e) => setLimitInput(e.target.value)}
            placeholder={`Default ${formatNumber(user.daily_limit)}`}
            className={numberFieldClass}
          />
          <Button
            onClick={() => {
              const trimmed = limitInput.trim();
              const value = trimmed === "" ? null : Math.max(0, Number(trimmed) || 0);
              apply({ limit_override: value }, "Limit saved");
            }}
            disabled={saving}
            size="sm"
            icon={Save}
          >
            Save
          </Button>
          <button
            type="button"
            onClick={() => apply({ limit_override: null }, "Override cleared")}
            disabled={saving}
            aria-label="Clear override"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-tg-hint transition active:bg-black/[0.04] active:text-red-500 disabled:opacity-50 dark:active:bg-white/[0.06]"
          >
            <Trash2 className="h-4 w-4" aria-hidden />
          </button>
        </div>
      </div>

      {/* Reset usage */}
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium text-tg-text">Today&rsquo;s usage</span>
        <Button
          onClick={() => apply({ reset_usage: true }, "Usage reset")}
          disabled={saving}
          variant="secondary"
          size="sm"
          icon={RotateCcw}
        >
          Reset
        </Button>
      </div>

      <div className="flex min-h-[1rem] justify-end">
        <SaveMessage status={status} message={saving ? "Saving…" : message} />
      </div>
    </div>
  );
}
