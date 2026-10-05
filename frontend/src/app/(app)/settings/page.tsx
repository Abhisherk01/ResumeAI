import type { Metadata } from "next";

import { ChangePasswordForm } from "@/components/settings/change-password-form";
import { UpdateProfileForm } from "@/components/settings/update-profile-form";

export const metadata: Metadata = { title: "Settings - ResumeAI" };

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-ink-soft">Manage your account.</p>
      </header>
      <div className="max-w-xl space-y-8">
        <UpdateProfileForm />
        <hr className="border-border" />
        <ChangePasswordForm />
      </div>
      <p className="text-xs text-ink-soft">
        Theme preferences live in the sidebar theme switcher. Email address
        changes arrive in a later phase (they require verifying the new
        address first).
      </p>
      <p className="text-xs text-ink-soft">
        Data controls (export/delete) are planned for Phase 10.
        {/* placeholder-copy honesty: the phases named here match the roadmap */}
      </p>
      <div className="h-4" />
    </div>
  );
}
