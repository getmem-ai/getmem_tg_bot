import { Smartphone } from "lucide-react";

/** Friendly screen shown when the app is opened outside Telegram (no initData). */
export function OpenInTelegram() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-8 text-center">
      <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-tg-button/10 text-tg-button">
        <Smartphone className="h-8 w-8" aria-hidden />
      </span>
      <h1 className="mt-5 text-lg font-semibold">Open inside Telegram</h1>
      <p className="mt-2 max-w-xs text-sm text-tg-hint">
        This mini app needs to be opened from the bot inside Telegram. Launch it
        from the bot&apos;s menu button or an inline button to continue.
      </p>
      <p className="mt-8 text-xs text-tg-hint">Powered by GetMem</p>
    </main>
  );
}
