export const THEMES = [
    { id: "plum-sky", label: "Plum & Sky" },
    { id: "soft-light", label: "Soft Light" },
    { id: "midnight", label: "Midnight" },
    { id: "indigo", label: "Indigo" },
    { id: "emerald", label: "Emerald" },
    { id: "violet", label: "Violet" },
  ] as const;

  export type ThemeId = (typeof THEMES)[number]["id"];

  export const DEFAULT_THEME: ThemeId = "plum-sky";
  export const THEME_STORAGE_KEY = "resumeai-theme";

  export function isThemeId(value: string | null): value is ThemeId {
    return THEMES.some((t) => t.id === value);
  }
