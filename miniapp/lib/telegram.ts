// Helpers for interacting with the raw Telegram WebApp object.
// We intentionally do NOT depend on @telegram-apps SDK to keep deps minimal.

export interface TelegramThemeParams {
  bg_color?: string;
  text_color?: string;
  hint_color?: string;
  link_color?: string;
  button_color?: string;
  button_text_color?: string;
  secondary_bg_color?: string;
}

export interface TelegramWebApp {
  initData: string;
  initDataUnsafe: Record<string, unknown>;
  themeParams: TelegramThemeParams;
  colorScheme: "light" | "dark";
  ready: () => void;
  expand: () => void;
  onEvent: (event: string, handler: () => void) => void;
  offEvent: (event: string, handler: () => void) => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  openTelegramLink?: (url: string) => void;
  openLink?: (url: string) => void;
  close?: () => void;
  HapticFeedback?: {
    impactOccurred?: (style: "light" | "medium" | "heavy" | "rigid" | "soft") => void;
    selectionChanged?: () => void;
    notificationOccurred?: (type: "error" | "success" | "warning") => void;
  };
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: TelegramWebApp;
    };
  }
}

/** Returns the Telegram WebApp object, or null when not running inside Telegram. */
export function getWebApp(): TelegramWebApp | null {
  if (typeof window === "undefined") return null;
  return window.Telegram?.WebApp ?? null;
}

/**
 * Returns the raw initData string to forward to the backend.
 * Falls back to NEXT_PUBLIC_DEV_INIT_DATA for local browser development.
 */
export function getInitData(): string {
  const wa = getWebApp();
  const fromTelegram = wa?.initData ?? "";
  if (fromTelegram) return fromTelegram;

  const dev = process.env.NEXT_PUBLIC_DEV_INIT_DATA;
  if (dev) return dev;

  return "";
}

/** True when we have usable initData (either from Telegram or the dev fallback). */
export function hasInitData(): boolean {
  return getInitData().length > 0;
}

/** Fires a light haptic tap if the Telegram bridge supports it. Never throws. */
export function haptic(
  style: "light" | "medium" | "heavy" | "rigid" | "soft" = "light",
): void {
  try {
    getWebApp()?.HapticFeedback?.impactOccurred?.(style);
  } catch {
    // Defensive: never crash if the bridge misbehaves.
  }
}

/** Fires a selection-change haptic (used when switching tabs). Never throws. */
export function hapticSelection(): void {
  try {
    getWebApp()?.HapticFeedback?.selectionChanged?.();
  } catch {
    // ignore
  }
}

/**
 * Sends the user back to the bot (for /upgrade etc.). Robust to missing APIs:
 * tries openTelegramLink, then openLink, then close(). Never throws.
 */
export function openBot(url?: string): void {
  const wa = getWebApp();
  try {
    if (url && wa?.openTelegramLink) {
      wa.openTelegramLink(url);
      return;
    }
    if (url && wa?.openLink) {
      wa.openLink(url);
      return;
    }
    wa?.close?.();
  } catch {
    // Defensive: never crash.
  }
}

const THEME_VAR_MAP: Array<[keyof TelegramThemeParams, string, string]> = [
  ["bg_color", "--tg-bg", "#ffffff"],
  ["text_color", "--tg-text", "#000000"],
  ["hint_color", "--tg-hint", "#707579"],
  ["link_color", "--tg-link", "#2481cc"],
  ["button_color", "--tg-button", "#2481cc"],
  ["button_text_color", "--tg-button-text", "#ffffff"],
  ["secondary_bg_color", "--tg-secondary-bg", "#f1f1f1"],
];

/** Maps Telegram themeParams onto CSS variables so the app matches the user's theme. */
export function applyTheme(wa: TelegramWebApp | null): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  const params = wa?.themeParams ?? {};

  for (const [key, cssVar, fallback] of THEME_VAR_MAP) {
    const value = params[key];
    root.style.setProperty(cssVar, value || fallback);
  }

  if (wa?.colorScheme) {
    root.style.colorScheme = wa.colorScheme;
  }
}

/**
 * Initialises the WebApp: ready(), expand(), apply theme, and subscribe to
 * theme changes. Returns a cleanup function. Safe to call when not in Telegram.
 */
export function initWebApp(onThemeChange?: () => void): () => void {
  const wa = getWebApp();
  applyTheme(wa);

  if (!wa) {
    return () => {};
  }

  try {
    wa.ready();
    wa.expand();
    if (wa.themeParams.bg_color && wa.setBackgroundColor) {
      wa.setBackgroundColor(wa.themeParams.bg_color);
    }
  } catch {
    // Defensive: never crash if the Telegram bridge misbehaves.
  }

  const handler = () => {
    applyTheme(getWebApp());
    onThemeChange?.();
  };

  wa.onEvent("themeChanged", handler);
  return () => {
    wa.offEvent("themeChanged", handler);
  };
}
