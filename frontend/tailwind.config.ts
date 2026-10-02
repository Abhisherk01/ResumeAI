import type { Config } from "tailwindcss";

/**
 * All colors reference CSS variables defined in src/app/globals.css.
 * Every theme (data-theme attribute) redefines those variables, so switching
 * a single attribute re-themes the entire app — no JS re-render needed.
 *
 * Class-name mapping (kept short for readability in JSX):
 *   bg-base        → --bg                bg-surface      → --surface
 *   text-ink       → --text-primary      text-ink-soft   → --text-secondary
 *   bg-accent      → --accent-primary    text-on-accent  → --accent-on
 *   bg-accent-soft → --accent-secondary  text-accent-soft-text → --accent-secondary-text
 */
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        base: "var(--bg)",
        surface: "var(--surface)",
        ink: "var(--text-primary)",
        "ink-soft": "var(--text-secondary)",
        accent: "var(--accent-primary)",
        "accent-on": "var(--accent-on)",
        "accent-soft": "var(--accent-secondary)",
        "accent-soft-text": "var(--accent-secondary-text)",
        border: "var(--border)",
        success: "var(--success)",
        warning: "var(--warning)",
        error: "var(--error)",
      },
      borderColor: {
        DEFAULT: "var(--border)",
      },
      boxShadow: {
        "neu-raised":
          "6px 6px 14px var(--shadow-dark), -6px -6px 14px var(--shadow-light)",
        "neu-raised-sm":
          "3px 3px 8px var(--shadow-dark), -3px -3px 8px var(--shadow-light)",
        "neu-inset":
          "inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light)",
      },
      borderRadius: {
        neu: "1rem",
        "neu-lg": "1.5rem",
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
    },
  },
  plugins: [
    // tailwindcss-animate will be re-added when we install animated shadcn
    // components (dialogs/toasts) in Step 2 — no component uses it yet.
  ],
};
export default config;
