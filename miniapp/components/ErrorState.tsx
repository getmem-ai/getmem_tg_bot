import type { ApiError } from "@/lib/api";

interface ErrorStateProps {
  error: ApiError;
  onRetry?: () => void;
}

/** A graceful, compact error card with an optional retry action. */
export function ErrorState({ error, onRetry }: ErrorStateProps) {
  const message =
    error.status === 0
      ? "Couldn't reach the server. Check your connection."
      : error.isUnauthorized
        ? "Your session couldn't be verified. Re-open the app from the bot."
        : "Something went wrong loading this.";

  return (
    <div className="rounded-card border border-red-500/20 bg-red-500/5 p-5 text-sm shadow-card">
      <p className="text-tg-text">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 rounded-2xl bg-brand px-4 py-2 text-xs font-semibold text-brand-fg shadow-pop transition active:scale-[0.99]"
        >
          Try again
        </button>
      )}
    </div>
  );
}
