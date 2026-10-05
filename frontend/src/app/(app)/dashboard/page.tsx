import type { Metadata } from "next";

import { AccountCard } from "@/components/dashboard/account-card";
import { GettingStarted } from "@/components/dashboard/getting-started";

export const metadata: Metadata = { title: "Dashboard - ResumeAI" };

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-ink-soft">
          Your resume workspace overview.
        </p>
      </header>
      <div className="grid gap-6 md:grid-cols-2">
        <AccountCard />
        <GettingStarted />
      </div>
    </div>
  );
}
