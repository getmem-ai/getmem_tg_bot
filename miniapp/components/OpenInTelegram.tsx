/** Friendly screen shown when the app is opened outside Telegram (no initData). */
export function OpenInTelegram() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-8 text-center">
      <div className="text-5xl" aria-hidden>
        📱
      </div>
      <h1 className="mt-4 text-lg font-semibold">Open inside Telegram</h1>
      <p className="mt-2 max-w-xs text-sm text-tg-hint">
        This mini app needs to be opened from the bot inside Telegram. Launch it
        from the bot&apos;s menu button or an inline button to continue.
      </p>
      <p className="mt-6 text-xs text-tg-hint">Powered by GetMem</p>
    </main>
  );
}
