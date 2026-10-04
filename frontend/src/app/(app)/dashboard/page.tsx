import type { Metadata } from "next";

export const metadata: Metadata = { title: "Dashboard - ResumeAI" };

export default function DashboardPage() {
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Dashboard</h1>
      <p className="text-sm text-ink-soft">
        Your resume overview arrives in Phase 4. Use the sidebar to explore
        Resumes and Settings.
      </p>
    </div>
  );
}
