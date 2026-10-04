"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  BarChart3,
  Briefcase,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
} from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider"; // ADDED
import { Button } from "@/components/ui/button"; // ADDED
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { Logo } from "./logo";
import { ThemeSwitcher } from "./theme-switcher";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/resumes", label: "Resumes", icon: FileText },
  { href: "/analyses", label: "Analyses", icon: BarChart3 },
  { href: "/matches", label: "Job Matches", icon: Briefcase },
  { href: "/settings", label: "Settings", icon: Settings },
];

function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav aria-label="Application" className="flex flex-col gap-1">
      {navItems.map(({ href, label, icon: Icon }) => {
        const isActive = pathname === href;
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? "page" : undefined}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-neu px-3 py-2.5 text-sm font-medium text-ink-soft transition-shadow",
              "hover:text-ink hover:shadow-neu-raised-sm",
              isActive && "bg-base text-accent shadow-neu-inset"
            )}
          >
            <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

// ADDED (7B-5): signed-in user identity + logout, wired to useAuth.
function SidebarUserBlock() {
  const { user, logout, isLoggingOut } = useAuth();
  if (!user) return null;
  return (
    <div className="rounded-neu bg-base p-3 shadow-neu-inset">
      <p className="truncate text-sm font-medium text-ink">{user.name}</p>
      <p className="truncate text-xs text-ink-soft">{user.email}</p>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        className="mt-3 w-full"
        loading={isLoggingOut}
        onClick={() => void logout()}
      >
        <LogOut className="h-4 w-4" aria-hidden="true" />
        Sign out
      </Button>
    </div>
  );
}

export function AppSidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      {/* Mobile top bar */}
      <header className="sticky top-0 z-40 flex items-center justify-between gap-3 border-b border-border bg-base px-4 py-3 lg:hidden">
        <Logo />
        <button
          type="button"
          aria-label="Open navigation menu"
          aria-expanded={mobileOpen}
          onClick={() => setMobileOpen(true)}
          className="inline-flex h-10 w-10 items-center justify-center rounded-neu bg-surface text-ink shadow-neu-raised-sm"
        >
          <Menu className="h-5 w-5" aria-hidden="true" />
        </button>
      </header>

      {/* Desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-64 flex-col border-r border-border bg-surface px-4 py-6 lg:flex">
        <Logo className="mb-8 px-1" />
        <SidebarNav />
        <div className="mt-auto space-y-4 pt-6">
          <SidebarUserBlock />
          <ThemeSwitcher align="start" />
        </div>
      </aside>

      {/* Mobile drawer (reuses the Dialog primitive as a left sheet) */}
      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <DialogContent className="inset-y-0 left-0 top-0 h-full max-w-xs translate-x-0 translate-y-0 rounded-neu-lg data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left">
          <DialogTitle className="sr-only">Application navigation</DialogTitle>
          <div className="flex h-full flex-col">
            <Logo className="mb-8" />
            <SidebarNav onNavigate={() => setMobileOpen(false)} />
            <div className="mt-auto space-y-4 pt-6">
              <SidebarUserBlock />
              <ThemeSwitcher align="start" />
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
