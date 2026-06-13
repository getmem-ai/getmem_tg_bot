import type { Config } from "tailwindcss";

/**
 * Design system — semantic tokens backed by CSS variables (see globals.css),
 * with a fixed light+dark indigo-blue + orange theme. The legacy `tg-*` names
 * are aliased onto the new tokens so older markup adopts the palette during the
 * migration; new/updated components use the semantic names below.
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
        bg: "var(--bg)",
        surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)", 3: "var(--surface-3)" },
        text: "var(--text)",
        muted: "var(--muted)",
        border: "var(--border)",
        "border-strong": "var(--border-strong)",
        primary: {
          DEFAULT: "var(--primary)",
          600: "var(--primary-600)",
          700: "var(--primary-700)",
          100: "var(--primary-100)",
          50: "var(--primary-50)",
          fg: "var(--on-primary)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          600: "var(--accent-600)",
          50: "var(--accent-50)",
          fg: "var(--on-accent)",
        },
        success: "var(--success)",
        warning: "var(--warning)",
        danger: "var(--danger)",
        // Legacy aliases → semantic tokens (so existing markup recolors).
        tg: {
          bg: "var(--surface)",
          text: "var(--text)",
          hint: "var(--muted)",
          link: "var(--primary)",
          button: "var(--primary)",
          "button-text": "var(--on-primary)",
          secondary: "var(--surface-2)",
        },
        // Legacy brand-* alias → primary (older components used brand).
        brand: {
          DEFAULT: "var(--primary)",
          50: "var(--primary-50)",
          100: "var(--primary-100)",
          500: "var(--primary)",
          600: "var(--primary-600)",
          700: "var(--primary-700)",
          fg: "var(--on-primary)",
        },
      },
      borderRadius: {
        card: "20px",
        "card-lg": "26px",
        pill: "999px",
      },
      boxShadow: {
        soft: "var(--shadow-soft)",
        card: "var(--shadow-card)",
        pop: "var(--shadow-pop)",
        ring: "var(--ring)",
      },
      backgroundImage: {
        primary: "linear-gradient(135deg, var(--primary) 0%, var(--primary-600) 100%)",
        accent: "linear-gradient(135deg, var(--accent) 0%, var(--accent-600) 100%)",
        hero: "linear-gradient(140deg, #2f6bff 0%, #1e4fd6 55%, #1840b0 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
