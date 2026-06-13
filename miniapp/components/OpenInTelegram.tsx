import Image from "next/image";

/** Friendly screen shown when the app is opened outside Telegram (no initData). */
export function OpenInTelegram() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center px-8 text-center">
      <span className="flex h-20 w-20 items-center justify-center rounded-card-lg bg-tg-bg shadow-card">
        <Image
          src="/brand/logo.png"
          alt=""
          width={56}
          height={56}
          className="h-14 w-14 object-contain"
          priority
        />
      </span>
      <h1 className="mt-6 text-lg font-bold">Open inside Telegram</h1>
      <p className="mt-2 max-w-xs text-sm leading-relaxed text-tg-hint">
        This mini app needs to be opened from the bot inside Telegram. Launch it
        from the bot&apos;s menu button or an inline button to continue.
      </p>
      <p className="mt-8 text-xs text-tg-hint">Powered by GetMem</p>
    </main>
  );
}
