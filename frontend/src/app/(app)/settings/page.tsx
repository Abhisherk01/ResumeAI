import type { Metadata } from "next";
import { Suspense } from "react";

import { EmailChangeConfirm } from "@/components/settings/email-change-confirm";
import { EmailChangeForm } from "@/components/settings/email-change-form";
import { ChangePasswordForm } from "@/components/settings/change-password-form";
import { SessionsSection } from "@/components/settings/sessions-section";
import { UpdateProfileForm } from "@/components/settings/update-profile-form";

export const metadata: Metadata = { title: "Settings - ResumeAI" };

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-ink-soft">Manage your account.</p>
      </header>
      {/* The emailed change link lands here (?email-token=...); the confirmer
          reads search params, so it needs the Suspense boundary. */}
      <Suspense fallback={null}>
        <EmailChangeConfirm />
      </Suspense>
      <div className="max-w-xl space-y-8">
        <UpdateProfileForm />
        <hr className="border-border" />
        <EmailChangeForm />
        <hr className="border-border" />
        <ChangePasswordForm />
        <hr className="border-border" />
        <SessionsSection />
      </div>
      <p className="text-xs text-ink-soft">
        Theme preferences live in the sidebar theme switcher.
      </p>
      <p className="text-xs text-ink-soft">
        Data controls (export/delete) are planned for Phase 10.
        {/* placeholder-copy honesty: the phases named here match the roadmap */}
      </p>
      <div className="h-4" />
    </div>
  );
}
