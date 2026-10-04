import type { Metadata } from "next";
import { Suspense } from "react";

import { ResetPasswordPanel } from "@/components/auth/reset-password-panel";

export const metadata: Metadata = { title: "Reset password - ResumeAI" };

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<p className="text-sm text-ink-soft">Loading...</p>}>
      <ResetPasswordPanel />
    </Suspense>
  );
}
