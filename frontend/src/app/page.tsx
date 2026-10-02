"use client";

import { useTheme } from "@/themes/theme-provider";
import { THEMES } from "@/themes/themes";

const swatches = [
  { label: "accent", className: "bg-accent" },
  { label: "accent-soft", className: "bg-accent-soft" },
  { label: "surface", className: "bg-surface border border-border" },
  { label: "success", className: "bg-success" },
  { label: "warning", className: "bg-warning" },
  { label: "error", className: "bg-error" },
];

export default function ThemePreviewPage() {
  const { theme, setTheme } = useTheme();

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="text-3xl font-bold tracking-tight">Theme system preview</h1>
      <p className="mt-2 text-ink-soft">
        Temporary verification page — replaced by the landing page in Step 4.
        Active theme: <span className="font-semibold text-accent">{theme}</span>
      </p>

      <div role="group" aria-label="Select theme" className="mt-6 flex flex-wrap gap-3">
        {THEMES.map((t) => (
          <button
            key={t.id}
            type="button"
            aria-pressed={theme === t.id}
            onClick={() => setTheme(t.id)}
            className={`rounded-neu bg-surface px-4 py-2 text-sm font-medium shadow-neu-raised-sm transition-shadow hover:shadow-neu-raised ${
              theme === t.id ? "shadow-neu-inset text-accent" : "text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <section className="mt-10 grid gap-6 sm:grid-cols-2">
        <div className="rounded-neu-lg bg-surface p-6 shadow-neu-raised">
          <h2 className="font-semibold">Raised card</h2>
          <p className="mt-1 text-sm text-ink-soft">
            Soft outer shadows in both directions — the core Neumorphic surface.
          </p>
        </div>
        <div className="rounded-neu-lg bg-surface p-6">
          <label htmlFor="demo-input" className="text-sm font-medium">
            Inset input
          </label>
          <input
            id="demo-input"
            placeholder="Type to feel the inset surface…"
            className="mt-2 w-full rounded-neu bg-base px-4 py-2 text-sm shadow-neu-inset placeholder:text-ink-soft"
          />
          <button
            type="button"
            className="mt-4 rounded-neu bg-accent px-4 py-2 text-sm font-medium text-on-accent shadow-neu-raised-sm hover:shadow-neu-raised disabled:cursor-not-allowed disabled:opacity-50"
          >
            Accent button
          </button>
        </div>
      </section>

      <section className="mt-10 rounded-neu-lg bg-surface p-6 shadow-neu-raised">
        <h2 className="font-semibold">Token swatches</h2>
        <div className="mt-4 flex flex-wrap gap-4">
          {swatches.map((s) => (
            <div key={s.label} className="text-center">
              <div className={`h-12 w-12 rounded-neu shadow-neu-inset ${s.className}`} />
              <p className="mt-1 text-xs text-ink-soft">{s.label}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
