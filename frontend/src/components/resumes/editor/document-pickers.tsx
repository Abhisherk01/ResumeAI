"use client";

/**
 * Template + accent pickers for the document editor (P8-6, D15).
 *
 * Chip buttons on a radiogroup pattern: keyboard-focusable buttons with
 * role="radio"/aria-checked - no new Radix surface, no dependencies.
 * Selection is IN-MEMORY until Save: the upsert PUT (D2) persists content
 * and presentation together, so nothing is stored on click alone.
 *
 * ACCENT_HEXES is the RENDER palette: the six fixed values applied by
 * backend/app/templates/css/shared.css.j2 (the same hexes WeasyPrint bakes
 * into the exported PDF). They are deliberately NOT app-theme tokens -
 * those retheme with data-theme; the document accent is document content
 * and must render identically under every app theme.
 * KEEP IN SYNC with shared.css.j2's .accent-* rules (pinned by test).
 */

import {
  RESUME_ACCENT_IDS,
  RESUME_TEMPLATE_IDS,
  type ResumeAccent,
  type ResumeTemplateId,
} from "@/lib/resumes/document-schema";
import { cn } from "@/lib/utils";

/** KEEP IN SYNC with .accent-* rules in backend shared.css.j2 (pin test). */
export const ACCENT_HEXES: Record<(typeof RESUME_ACCENT_IDS)[number], string> = {
  blue: "#2563eb",
  teal: "#0f766e",
  green: "#15803d",
  amber: "#b45309",
  rose: "#be123c",
  violet: "#6d28d9",
};

const TEMPLATE_LABELS: Record<ResumeTemplateId, string> = {
  classic: "Classic",
  modern: "Modern",
  compact: "Compact",
  creative: "Creative",
};

const ACCENT_LABELS: Record<ResumeAccent, string> = {
  blue: "Blue",
  teal: "Teal",
  green: "Green",
  amber: "Amber",
  rose: "Rose",
  violet: "Violet",
};

const chipClasses = (selected: boolean) =>
  cn(
    "rounded-neu px-4 py-2 text-sm font-medium transition-shadow",
    selected
      ? "bg-base text-accent shadow-neu-inset"
      : "text-ink-soft shadow-neu-raised-sm hover:shadow-neu-raised"
  );

export function TemplatePicker({
  value,
  onChange,
}: {
  value: ResumeTemplateId;
  onChange: (id: ResumeTemplateId) => void;
}) {
  return (
    <div className="space-y-2">
      <p id="template-picker-label" className="text-sm font-medium text-ink">
        Template
      </p>
      <div
        role="radiogroup"
        aria-labelledby="template-picker-label"
        className="flex flex-wrap gap-2"
      >
        {RESUME_TEMPLATE_IDS.map((id) => (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={value === id}
            className={chipClasses(value === id)}
            onClick={() => onChange(id)}
          >
            {TEMPLATE_LABELS[id]}
          </button>
        ))}
      </div>
    </div>
  );
}

export function AccentPicker({
  value,
  onChange,
}: {
  value: ResumeAccent;
  onChange: (accent: ResumeAccent) => void;
}) {
  return (
    <div className="space-y-2">
      <p id="accent-picker-label" className="text-sm font-medium text-ink">
        Accent color
      </p>
      <div
        role="radiogroup"
        aria-labelledby="accent-picker-label"
        className="flex flex-wrap gap-3"
      >
        {RESUME_ACCENT_IDS.map((id) => (
          <button
            key={id}
            type="button"
            role="radio"
            aria-checked={value === id}
            aria-label={`${ACCENT_LABELS[id]} accent`}
            onClick={() => onChange(id)}
            className={cn(
              "h-7 w-7 rounded-full border border-border transition-shadow",
              value === id && "ring-2 ring-accent ring-offset-2 ring-offset-base"
            )}
            style={{ backgroundColor: ACCENT_HEXES[id] }}
          />
        ))}
      </div>
    </div>
  );
}