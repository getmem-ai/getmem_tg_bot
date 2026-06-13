import type { Config } from "tailwindcss";

/**
 * Design system tokens. Surfaces/text use the Telegram theme variables (so the
 * app adapts to the user's light/dark theme), while the brand accent is a
 * constant violet for a cohesive, branded look across themes.
 */
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme-adaptive (from Telegram).
        tg: {
          bg: "var(--tg-bg)",
          text: "var(--tg-text)",
          hint: "var(--tg-hint)",
          link: "var(--tg-link)",
          button: "var(--tg-button)",
          "button-text": "var(--tg-button-text)",
          secondary: "var(--tg-secondary-bg)",
        },
        // Constant brand ramp (violet).
        brand: {
          DEFAULT: "#7c5cfc",
          50: "#f3f1ff",
          100: "#e9e5ff",
          200: "#d6ccff",
          300: "#b9a8ff",
          400: "#9b82fb",
          500: "#7c5cfc",
          600: "#6b46f0",
          700: "#5a37d6",
          800: "#4a2fb0",
          900: "#3d2a8c",
          fg: "#ffffff",
        },
      },
      borderRadius: {
        card: "20px",
        "card-lg": "28px",
      },
      boxShadow: {
        soft: "0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06)",
        card: "0 6px 20px rgba(17,12,46,.07)",
        pop: "0 10px 28px rgba(124,92,252,.30)",
        ring: "0 0 0 4px rgba(124,92,252,.16)",
      },
      backgroundImage: {
        brand: "linear-gradient(135deg,#7c5cfc 0%,#5b4be0 100%)",
        "brand-soft": "linear-gradient(135deg,#8f73ff 0%,#6b46f0 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
