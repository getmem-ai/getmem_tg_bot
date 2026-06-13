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
        // Lighter, softer gradients (avoid heavy flat fills).
        "grad-primary":
          "linear-gradient(135deg, #4f86ff 0%, #2f6bff 60%, #1e4fd6 100%)",
        "grad-accent":
          "linear-gradient(135deg, #ffa45c 0%, #ff8a3d 60%, #f2701a 100%)",
        hero: "linear-gradient(140deg, #5b8cff 0%, #2f6bff 55%, #2257e0 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
