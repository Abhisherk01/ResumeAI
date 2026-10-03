"use client";

import { Check, Palette } from "lucide-react";

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import { useTheme } from "@/themes/theme-provider";
import { THEMES } from "@/themes/themes";

export function ThemeSwitcher({ align = "end" }: { align?: "start" | "center" | "end" }) {
  const { theme, setTheme } = useTheme();
  const current = THEMES.find((t) => t.id === theme);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        aria-label="Change color theme"
        className={cn(
          "inline-flex h-10 items-center gap-2 rounded-neu bg-surface px-3 text-sm font-medium text-ink",
          "shadow-neu-raised-sm transition-shadow hover:shadow-neu-raised focus-visible:shadow-neu-inset"
        )}
      >
        <Palette className="h-4 w-4" aria-hidden="true" />
        <span className="hidden sm:inline">{current?.label}</span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align={align}>
        <DropdownMenuLabel>Theme</DropdownMenuLabel>
        {THEMES.map((t) => (
          <DropdownMenuItem key={t.id} onSelect={() => setTheme(t.id)}>
            <span className="flex-1">{t.label}</span>
            {theme === t.id && <Check className="h-4 w-4 text-accent" aria-hidden="true" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
